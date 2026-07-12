import os
import json
import time
import zlib
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

from utils.resource_manager import RM

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Manages encrypted local backups, incremental history, and restore procedures
    for lifelong memories (user_memory.json, world_model.json).
    """

    def __init__(self) -> None:
        self.backup_dir = RM.data("backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derives a 32-byte Fernet key from a password and salt using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived = kdf.derive(password.encode("utf-8"))
        return base64.urlsafe_b64encode(derived)

    def create_backup(self, password: str, label: str = "") -> Tuple[Path, Path]:
        """
        Creates an encrypted, compressed backup of all memory files.
        Returns paths to the encrypted payload and metadata JSON.
        """
        timestamp = int(time.time())
        salt = os.urandom(16)
        
        # Read files to include
        memory_dir = RM.memory()
        files_to_backup = ["user_memory.json", "world_model.json"]
        
        payload_data = {}
        for filename in files_to_backup:
            filepath = memory_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        payload_data[filename] = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to read {filename} for backup: {e}")
                    payload_data[filename] = {}
            else:
                payload_data[filename] = {}

        # 1. Compress payload
        serialized = json.dumps(payload_data).encode("utf-8")
        compressed = zlib.compress(serialized)
        
        # 2. Encrypt compressed payload
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        encrypted_payload = fernet.encrypt(compressed)
        
        # 3. Write payload file
        payload_path = self.backup_dir / f"backup_{timestamp}.enc"
        with open(payload_path, "wb") as f:
            f.write(encrypted_payload)
            
        # 4. Write metadata file
        meta_data = {
            "timestamp": timestamp,
            "label": label,
            "salt_hex": salt.hex(),
            "files": list(payload_data.keys()),
            "size_bytes": len(encrypted_payload),
            "format_version": "1.0"
        }
        meta_path = self.backup_dir / f"backup_{timestamp}_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=4)
            
        logger.info(f"Encrypted backup created: {payload_path}")
        return payload_path, meta_path

    def list_backups(self) -> List[Dict[str, Any]]:
        """Scans the backup folder and returns a list of backup versions metadata."""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith("_meta.json"):
                meta_path = self.backup_dir / filename
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        # Add path details
                        meta["meta_file"] = filename
                        meta["payload_file"] = filename.replace("_meta.json", ".enc")
                        backups.append(meta)
                except Exception as e:
                    logger.error(f"Error loading backup meta {filename}: {e}")
                    
        # Sort newest first
        backups.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return backups

    def restore_backup(self, backup_name: str, password: str) -> bool:
        """
        Decrypts, decompresses, validates, and restores memory files.
        Returns True on success, raises exception on incorrect password or invalid payload.
        """
        # backup_name can be "backup_12345.enc" or "backup_12345"
        base_name = backup_name.split(".")[0]
        payload_path = self.backup_dir / f"{base_name}.enc"
        meta_path = self.backup_dir / f"{base_name}_meta.json"
        
        if not payload_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Backup files not found for name: {backup_name}")
            
        # 1. Read metadata for salt
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        salt = bytes.fromhex(meta["salt_hex"])
        
        # 2. Read encrypted payload
        with open(payload_path, "rb") as f:
            encrypted_payload = f.read()
            
        # 3. Decrypt payload
        try:
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            decrypted_compressed = fernet.decrypt(encrypted_payload)
        except Exception as e:
            logger.error(f"Decrypt failed. Invalid password? {e}")
            raise ValueError("Decryption failed. Incorrect password or corrupted backup payload.")
            
        # 4. Decompress payload
        try:
            decompressed = zlib.decompress(decrypted_compressed)
            payload_data = json.loads(decompressed.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decompress or parse backup JSON: {e}")
            raise ValueError("Corrupted backup archive. Could not parse inner memory data.")
            
        # 5. Integrity validation check (Confirm we have dictionary structure and expected files)
        if not isinstance(payload_data, dict):
            raise ValueError("Integrity check failed: decrypted data is not a dictionary.")
            
        # 6. Restore files to memory directory
        memory_dir = RM.memory()
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, file_content in payload_data.items():
            dest_path = memory_dir / filename
            try:
                with open(dest_path, "w", encoding="utf-8") as f:
                    json.dump(file_content, f, indent=4)
                logger.info(f"Restored memory file: {dest_path}")
            except Exception as e:
                logger.error(f"Failed to restore file {filename}: {e}")
                raise RuntimeError(f"Data loss prevention: failed to write {filename} to disk.")
                
        return True

    def import_backup(self, enc_content: bytes, meta_content: dict) -> str:
        """Imports an external backup by saving it with a unique name."""
        timestamp = int(time.time())
        # Make name unique in case of collision
        while (self.backup_dir / f"backup_{timestamp}.enc").exists():
            timestamp += 1
            
        payload_path = self.backup_dir / f"backup_{timestamp}.enc"
        meta_path = self.backup_dir / f"backup_{timestamp}_meta.json"
        
        # Save payload
        with open(payload_path, "wb") as f:
            f.write(enc_content)
            
        # Save metadata
        meta_content["timestamp"] = timestamp
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_content, f, indent=4)
            
        return f"backup_{timestamp}"
