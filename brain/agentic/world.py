import logging
import json
import os
import time
import uuid
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from utils.resource_manager import RM

logger = logging.getLogger(__name__)

class WorldModel:
    """
    Connected Knowledge Graph representing entities (Projects, Goals, People, Places, Habits)
    and their categorized relationships. Loaded and saved persistently in user memory.
    """
    
    def __init__(self):
        # adjacency list for the graph: node_id -> set of connected node_ids
        self.graph: Dict[str, Set[str]] = {}
        # node storage: node_id -> {"label": str, "metadata": Dict}
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # edge relationships: "min_id-max_id" -> relation_label_string
        self.edges: Dict[str, str] = {}
        
        self.load()
        
    def add_node(self, node_id: str, label: str, metadata: Dict[str, Any]) -> None:
        self.nodes[node_id] = {"label": label, "metadata": metadata}
        if node_id not in self.graph:
            self.graph[node_id] = set()
            
    def add_edge(self, node_id_1: str, node_id_2: str, relation: str = "relates_to") -> None:
        if node_id_1 in self.nodes and node_id_2 in self.nodes:
            # Add to adjacency graph
            self.graph[node_id_1].add(node_id_2)
            self.graph[node_id_2].add(node_id_1)
            
            # Save relationship label
            key = f"{min(node_id_1, node_id_2)}-{max(node_id_1, node_id_2)}"
            self.edges[key] = relation
            
    def delete_node(self, node_id: str) -> None:
        if node_id in self.nodes:
            del self.nodes[node_id]
        if node_id in self.graph:
            # Remove all edges to this node
            for neighbor in list(self.graph[node_id]):
                if neighbor in self.graph:
                    self.graph[neighbor].discard(node_id)
                    key = f"{min(node_id, neighbor)}-{max(node_id, neighbor)}"
                    self.edges.pop(key, None)
            del self.graph[node_id]
        self.save()

    def delete_edge(self, node_id_1: str, node_id_2: str) -> None:
        if node_id_1 in self.graph:
            self.graph[node_id_1].discard(node_id_2)
        if node_id_2 in self.graph:
            self.graph[node_id_2].discard(node_id_1)
        key = f"{min(node_id_1, node_id_2)}-{max(node_id_1, node_id_2)}"
        self.edges.pop(key, None)
        self.save()

    def save(self) -> None:
        """Persists the graph nodes and edges to user memory."""
        try:
            # Convert set to list for JSON serialization
            serialized_graph = {n_id: list(neighbors) for n_id, neighbors in self.graph.items()}
            data = {
                "nodes": self.nodes,
                "graph": serialized_graph,
                "edges": self.edges
            }
            mem_dir = RM.memory()
            mem_dir.mkdir(parents=True, exist_ok=True)
            path = mem_dir / "world_model.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info("WorldModel saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save WorldModel: {e}")

    def load(self) -> None:
        """Loads node/edge configuration from memory folder."""
        path = RM.memory() / "world_model.json"
        if not path.exists():
            self._load_default_graph()
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.nodes = data.get("nodes", {})
            self.edges = data.get("edges", {})
            serialized_graph = data.get("graph", {})
            self.graph = {n_id: set(neighbors) for n_id, neighbors in serialized_graph.items()}
            logger.info("WorldModel loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load WorldModel: {e}. Seeding default.")
            self._load_default_graph()

    def _load_default_graph(self) -> None:
        """Seeds standard project and context nodes for instant connectivity."""
        self.nodes.clear()
        self.graph.clear()
        self.edges.clear()
        
        self.add_node("u1", "User", {"name": "Faisal", "importance": "Critical"})
        self.add_node("p1", "Project", {"name": "Khushi AI", "description": "Desktop AI assistant", "importance": "High"})
        self.add_node("p2", "Project", {"name": "UPSC Preparation", "description": "Civil Services Prep studies", "importance": "Critical"})
        self.add_node("g1", "Goal", {"name": "Build local API server", "importance": "Medium"})
        self.add_node("g2", "Goal", {"name": "Crack UPSC Exam", "importance": "Critical"})
        self.add_node("h1", "Habit", {"name": "Daily coding practice", "frequency": "daily", "importance": "Medium"})
        self.add_node("h2", "Habit", {"name": "Study Polity daily", "frequency": "daily", "importance": "High"})
        self.add_node("pl1", "Place", {"name": "New Delhi", "importance": "Medium"})

        self.add_edge("u1", "p1", "is working on")
        self.add_edge("u1", "p2", "is preparing for")
        self.add_edge("u1", "pl1", "lives in")
        self.add_edge("p1", "g1", "aims to achieve")
        self.add_edge("p2", "g2", "aims to achieve")
        self.add_edge("p1", "h1", "requires habit")
        self.add_edge("p2", "h2", "requires habit")
        self.save()

    def semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """Matches nodes using clean word-token match score across name and description."""
        query_words = set(query.lower().split())
        if not query_words:
            return []

        results = []
        for n_id, n_data in self.nodes.items():
            node_name = n_data.get("metadata", {}).get("name", "").lower()
            node_desc = n_data.get("metadata", {}).get("description", "").lower()
            node_val = str(n_data.get("metadata", {}).get("value", "")).lower()
            node_label = n_data.get("label", "").lower()
            
            target_text = f"{n_id} {node_name} {node_desc} {node_val} {node_label}"
            target_words = set(target_text.split())
            
            intersection = query_words.intersection(target_words)
            if intersection:
                score = len(intersection) / len(query_words)
                results.append((score, n_id, n_data))
                
        results.sort(key=lambda x: x[0], reverse=True)
        return [{"id": r[1], **r[2], "score": r[0]} for r in results]

    def merge_memory(self, label: str, name: str, metadata: Dict[str, Any], relation_to_id: str = None, relation_type: str = "relates_to") -> str:
        """Merges new memory values into existing same-name entity or spawns a new node."""
        existing_id = None
        for n_id, n_data in self.nodes.items():
            if n_data["label"].lower() == label.lower():
                existing_name = n_data.get("metadata", {}).get("name", "").lower()
                if existing_name == name.lower():
                    existing_id = n_id
                    break
                    
        if existing_id:
            self.nodes[existing_id]["metadata"].update(metadata)
            self.nodes[existing_id]["metadata"]["updated_at"] = time.time()
            node_id = existing_id
            logger.info(f"Merged metadata into node: {node_id}")
        else:
            node_id = f"{label.lower()}_{int(time.time())}_{uuid.uuid4().hex[:4]}"
            metadata["name"] = name
            metadata["created_at"] = time.time()
            metadata["updated_at"] = time.time()
            self.add_node(node_id, label, metadata)
            logger.info(f"Created new knowledge node: {node_id}")

        if relation_to_id and relation_to_id in self.nodes:
            self.add_edge(node_id, relation_to_id, relation_type)
            
        self.save()
        return node_id

    def check_conflict(self, label: str, name: str, value: str) -> Optional[Dict[str, Any]]:
        """Checks for conflicting data of same-name label values (e.g. location clash)."""
        for n_id, n_data in self.nodes.items():
            if n_data["label"].lower() == label.lower():
                existing_name = n_data.get("metadata", {}).get("name", "").lower()
                if existing_name == name.lower():
                    existing_val = n_data.get("metadata", {}).get("value")
                    if existing_val and str(existing_val).lower() != str(value).lower():
                        return {
                            "node_id": n_id,
                            "field": "value",
                            "existing_value": existing_val,
                            "new_value": value,
                            "message": f"Conflict detected on '{name}': existing is '{existing_val}', new is '{value}'."
                        }
        return None

    def query_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        results = []
        target_id = None
        
        for n_id, n_data in self.nodes.items():
            node_name = n_data.get("metadata", {}).get("name", "").lower()
            if entity_name.lower() in node_name or entity_name.lower() in n_data["label"].lower():
                target_id = n_id
                break
                
        if target_id and target_id in self.graph:
            for neighbor_id in self.graph[target_id]:
                results.append({"id": neighbor_id, **self.nodes[neighbor_id]})
                
        return results

    def explain_relationship(self, entity_name: str) -> str:
        """Builds a human-readable list explaining the direct links of an entity."""
        target_id = None
        target_data = None
        for n_id, n_data in self.nodes.items():
            node_name = n_data.get("metadata", {}).get("name", "").lower()
            if entity_name.lower() in node_name or entity_name.lower() in n_data["label"].lower():
                target_id = n_id
                target_data = n_data
                break
                
        if not target_id:
            return f"I couldn't find '{entity_name}' in my knowledge graph."
            
        neighbors = self.graph.get(target_id, set())
        if not neighbors:
            return f"'{target_data['metadata'].get('name', entity_name)}' is currently not connected to any other entities."
            
        explanations = []
        name_1 = target_data["metadata"].get("name", target_data["label"])
        
        for n_id in neighbors:
            neighbor_data = self.nodes[n_id]
            name_2 = neighbor_data["metadata"].get("name", neighbor_data["label"])
            key = f"{min(target_id, n_id)}-{max(target_id, n_id)}"
            rel_label = self.edges.get(key, "is connected to")
            explanations.append(f"- '{name_1}' {rel_label} '{name_2}' (Type: {neighbor_data['label']})")
            
        return f"Here is how '{name_1}' relates to other information:\n" + "\n".join(explanations)
