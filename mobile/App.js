import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, Image, ActivityIndicator, Alert, SafeAreaView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';

export default function App() {
  // Connection states
  const [serverUrl, setServerUrl] = useState('http://192.168.1.10:8000');
  const [apiToken, setApiToken] = useState('');
  const [paired, setPaired] = useState(false);
  const [connecting, setConnecting] = useState(false);

  // Desktop telemetry
  const [telemetry, setTelemetry] = useState(null);
  const [desktopName, setDesktopName] = useState('Desktop');

  // Navigation tab
  const [activeTab, setActiveTab] = useState('dashboard');

  // Chat
  const [chatMessage, setChatMessage] = useState('');
  const [chatLog, setChatLog] = useState([
    { id: '1', sender: 'assistant', text: 'Hello Faisal, your mobile companion is paired.' }
  ]);

  // Tasks & Goals
  const [tasks, setTasks] = useState({});
  const [newTaskKey, setNewTaskKey] = useState('');
  const [newTaskVal, setNewTaskVal] = useState('');
  const [goals, setGoals] = useState({ agentic_goals: [], companion_goals: [] });

  // Media & Files
  const [filesList, setFilesList] = useState([]);
  const [sharedFileName, setSharedFileName] = useState('');
  const [sharedFileContent, setSharedFileContent] = useState('');
  const [selectedFileContent, setSelectedFileContent] = useState(null);
  const [lastScreenshotUrl, setLastScreenshotUrl] = useState(null);
  const [screenshotLoading, setScreenshotLoading] = useState(false);

  // Clipboard
  const [clipboardText, setClipboardText] = useState('');

  // Push Notifications / Events Log
  const [eventsLog, setEventsLog] = useState([
    { timestamp: new Date().toLocaleTimeString(), topic: 'SYSTEM', detail: 'Mobile client launched.' }
  ]);

  // WebSocket reference
  const wsRef = useRef(null);

  // On mount: check for saved credentials
  useEffect(() => {
    async function loadCredentials() {
      try {
        const savedUrl = await AsyncStorage.getItem('KHUSHI_SERVER_URL');
        const savedToken = await AsyncStorage.getItem('KHUSHI_API_TOKEN');
        if (savedUrl && savedToken) {
          setServerUrl(savedUrl);
          setApiToken(savedToken);
          // Try auto-pair
          pairServer(savedUrl, savedToken);
        }
      } catch (e) {
        console.log('Failed to load credentials', e);
      }
    }
    loadCredentials();
  }, []);

  // Poll status & sync when paired
  useEffect(() => {
    if (!paired) return;

    // Fetch status initially
    fetchStatus();

    // Set up polling interval
    const interval = setInterval(() => {
      fetchStatus();
    }, 5000);

    // Initialize events WebSocket
    connectEventsWS();

    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
    };
  }, [paired]);

  // Secure Pairing
  async function pairServer(url = serverUrl, token = apiToken) {
    if (!url || !token) {
      Alert.alert('Error', 'Please enter both the server URL and API Token.');
      return;
    }
    setConnecting(true);
    // Trim slashes from url
    const formattedUrl = url.replace(/\/+$/, '');
    try {
      const response = await fetch(`${formattedUrl}/api/pair`, {
        method: 'GET',
        headers: { 'x-api-key': token }
      });
      if (response.status === 200) {
        const data = await response.json();
        setDesktopName(data.desktop_name || 'Desktop');
        setServerUrl(formattedUrl);
        setApiToken(token);
        await AsyncStorage.setItem('KHUSHI_SERVER_URL', formattedUrl);
        await AsyncStorage.setItem('KHUSHI_API_TOKEN', token);
        setPaired(true);
      } else {
        Alert.alert('Connection Failed', `Server returned code: ${response.status}`);
      }
    } catch (err) {
      Alert.alert('Connection Error', 'Could not reach server. Verify IP, Port, and LAN connection.');
    } finally {
      setConnecting(false);
    }
  }

  // Disconnect
  async function disconnectServer() {
    await AsyncStorage.removeItem('KHUSHI_SERVER_URL');
    await AsyncStorage.removeItem('KHUSHI_API_TOKEN');
    setPaired(false);
    setTelemetry(null);
    setGoals({ agentic_goals: [], companion_goals: [] });
    setTasks({});
    if (wsRef.current) wsRef.current.close();
  }

  // Fetch telemetry status
  async function fetchStatus() {
    try {
      const response = await fetch(`${serverUrl}/status`, {
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        const data = await response.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.log('Status polling failed', err);
    }
  }

  // Event Push Notifications WS
  function connectEventsWS() {
    if (wsRef.current) wsRef.current.close();

    const wsUrl = serverUrl.replace(/^http/, 'ws') + `/events?token=${apiToken}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const newEvent = {
          timestamp: new Date().toLocaleTimeString(),
          topic: payload.topic || 'ALERT',
          detail: JSON.stringify(payload.data || payload)
        };
        setEventsLog(prev => [newEvent, ...prev].slice(0, 50));
      } catch (err) {
        console.log('Failed to parse WS event', err);
      }
    };

    ws.onerror = (e) => console.log('Events WS Error', e);
    ws.onclose = () => {
      // Auto-reconnect if still paired after 5s
      setTimeout(() => {
        if (paired) connectEventsWS();
      }, 5000);
    };
  }

  // Chat Submission
  async function sendChatMessage() {
    if (!chatMessage.trim()) return;
    const msg = chatMessage;
    setChatMessage('');
    setChatLog(prev => [...prev, { id: Date.now().toString(), sender: 'user', text: msg }]);

    try {
      const response = await fetch(`${serverUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiToken
        },
        body: JSON.stringify({ message: msg })
      });
      if (response.status === 200) {
        const data = await response.json();
        setChatLog(prev => [...prev, { id: (Date.now() + 1).toString(), sender: 'assistant', text: data.response }]);
      } else {
        setChatLog(prev => [...prev, { id: (Date.now() + 1).toString(), sender: 'assistant', text: 'Error executing message.' }]);
      }
    } catch (err) {
      setChatLog(prev => [...prev, { id: (Date.now() + 1).toString(), sender: 'assistant', text: 'Network connection lost.' }]);
    }
  }

  // Control Desktop command via Chat Intent
  async function runDesktopIntent(command) {
    try {
      await fetch(`${serverUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiToken
        },
        body: JSON.stringify({ message: command })
      });
      // Append command to event log for UI feedback
      setEventsLog(prev => [{
        timestamp: new Date().toLocaleTimeString(),
        topic: 'CONTROL',
        detail: `Sent desktop command: "${command}"`
      }, ...prev]);
    } catch (err) {
      Alert.alert('Control Error', 'Could not send command to desktop.');
    }
  }

  // Capture Desktop Screenshot
  async function captureScreenshot() {
    setScreenshotLoading(true);
    try {
      // Append a cache-buster timestamp query
      const url = `${serverUrl}/desktop/screenshot?token=${apiToken}&t=${Date.now()}`;
      setLastScreenshotUrl(url);
    } catch (err) {
      Alert.alert('Error', 'Failed to retrieve desktop screen.');
    } finally {
      setScreenshotLoading(false);
    }
  }

  // Sync tasks
  async function loadTasks() {
    try {
      const response = await fetch(`${serverUrl}/tasks`, {
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        const data = await response.json();
        setTasks(data.tasks || {});
      }
    } catch (err) {
      console.log('Error loading tasks', err);
    }
  }

  // Save task
  async function addTask() {
    if (!newTaskKey.trim() || !newTaskVal.trim()) return;
    try {
      const response = await fetch(`${serverUrl}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiToken
        },
        body: JSON.stringify({
          key: newTaskKey.trim(),
          value: newTaskVal.trim(),
          category: 'tasks'
        })
      });
      if (response.status === 200) {
        setNewTaskKey('');
        setNewTaskVal('');
        loadTasks();
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to add task.');
    }
  }

  // Delete task
  async function deleteTask(key) {
    try {
      const response = await fetch(`${serverUrl}/tasks/${key}`, {
        method: 'DELETE',
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        loadTasks();
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to delete task.');
    }
  }

  // Sync goals
  async function loadGoals() {
    try {
      const response = await fetch(`${serverUrl}/goals`, {
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        const data = await response.json();
        setGoals(data);
      }
    } catch (err) {
      console.log('Error loading goals', err);
    }
  }

  // Media - Upload Camera simulation
  async function simulateCameraUpload() {
    const formData = new FormData();
    formData.append('file', {
      uri: 'mock-camera-uri',
      name: `camera_${Date.now()}.jpg`,
      type: 'image/jpeg'
    });

    try {
      const response = await fetch(`${serverUrl}/upload/camera`, {
        method: 'POST',
        headers: {
          'x-api-key': apiToken
        },
        body: formData
      });
      if (response.status === 200) {
        Alert.alert('Success', 'Camera image uploaded successfully to desktop.');
      } else {
        Alert.alert('Upload Failed', `Server code: ${response.status}`);
      }
    } catch (err) {
      Alert.alert('Upload Error', 'Could not upload camera image.');
    }
  }

  // Media - Upload Screenshot simulation
  async function simulateScreenshotUpload() {
    const formData = new FormData();
    formData.append('file', {
      uri: 'mock-screenshot-uri',
      name: `screenshot_${Date.now()}.jpg`,
      type: 'image/jpeg'
    });

    try {
      const response = await fetch(`${serverUrl}/upload/screenshot`, {
        method: 'POST',
        headers: {
          'x-api-key': apiToken
        },
        body: formData
      });
      if (response.status === 200) {
        Alert.alert('Success', 'Screenshot uploaded successfully.');
      }
    } catch (err) {
      Alert.alert('Upload Error', 'Failed to upload screenshot.');
    }
  }

  // File Transfer - Load files
  async function loadSharedFiles() {
    try {
      const response = await fetch(`${serverUrl}/files`, {
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        const data = await response.json();
        setFilesList(data.files || []);
      }
    } catch (err) {
      console.log('Error loading files', err);
    }
  }

  // File Transfer - Upload Text File
  async function uploadTextFile() {
    if (!sharedFileName.trim() || !sharedFileContent.trim()) return;
    
    // Create text file blob simulation using FormData
    const formData = new FormData();
    formData.append('file', {
      uri: 'data:text/plain;charset=utf-8,' + encodeURIComponent(sharedFileContent),
      name: sharedFileName.endsWith('.txt') ? sharedFileName : `${sharedFileName}.txt`,
      type: 'text/plain'
    });

    try {
      const response = await fetch(`${serverUrl}/files/upload`, {
        method: 'POST',
        headers: { 'x-api-key': apiToken },
        body: formData
      });
      if (response.status === 200) {
        setSharedFileName('');
        setSharedFileContent('');
        loadSharedFiles();
        Alert.alert('Success', 'File uploaded to desktop shared space.');
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to upload file.');
    }
  }

  // File Transfer - Download file
  async function downloadSharedFile(filename) {
    try {
      const response = await fetch(`${serverUrl}/files/download/${filename}`, {
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        const text = await response.text();
        setSelectedFileContent({ name: filename, content: text });
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to download file content.');
    }
  }

  // Clipboard sync GET
  async function syncClipboardGet() {
    try {
      const response = await fetch(`${serverUrl}/clipboard`, {
        headers: { 'x-api-key': apiToken }
      });
      if (response.status === 200) {
        const data = await response.json();
        setClipboardText(data.text || '');
        Alert.alert('Clipboard Synced', `Received clipboard: "${data.text}"`);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to get desktop clipboard.');
    }
  }

  // Clipboard sync POST
  async function syncClipboardSet() {
    if (!clipboardText) return;
    try {
      const response = await fetch(`${serverUrl}/clipboard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiToken
        },
        body: JSON.stringify({ text: clipboardText })
      });
      if (response.status === 200) {
        Alert.alert('Clipboard Synced', 'Mobile clipboard pushed to Desktop.');
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to push clipboard.');
    }
  }

  // Simulated Voice dictation file upload
  async function simulateVoiceDictation() {
    const formData = new FormData();
    formData.append('file', {
      uri: 'mock-audio-wav',
      name: 'voice_command.wav',
      type: 'audio/wav'
    });

    try {
      const response = await fetch(`${serverUrl}/voice/remote`, {
        method: 'POST',
        headers: { 'x-api-key': apiToken },
        body: formData
      });
      if (response.status === 200) {
        const data = await response.json();
        // Add both user transcript and response to chat
        setChatLog(prev => [
          ...prev,
          { id: Date.now().toString(), sender: 'user', text: `[Voice] ${data.text}` },
          { id: (Date.now() + 1).toString(), sender: 'assistant', text: data.response }
        ]);
        setActiveTab('chat');
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to send remote voice clip.');
    }
  }

  // Render content according to tab
  function renderTabContent() {
    switch (activeTab) {
      case 'dashboard':
        return (
          <ScrollView style={styles.scrollContainer} contentContainerStyle={{ paddingBottom: 30 }}>
            {/* System Telemetry */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Desktop System Health</Text>
              <View style={styles.telemetryGrid}>
                <View style={styles.telemetryItem}>
                  <Text style={styles.telemetryVal}>{telemetry?.system_info?.cpu_percent ?? 'N/A'}%</Text>
                  <Text style={styles.telemetryLbl}>CPU Usage</Text>
                </View>
                <View style={styles.telemetryItem}>
                  <Text style={styles.telemetryVal}>{telemetry?.system_info?.ram_percent ?? 'N/A'}%</Text>
                  <Text style={styles.telemetryLbl}>RAM Usage</Text>
                </View>
                <View style={styles.telemetryItem}>
                  <Text style={styles.telemetryVal}>{telemetry?.system_info?.battery_percent ?? 'N/A'}%</Text>
                  <Text style={styles.telemetryLbl}>Battery</Text>
                </View>
                <View style={styles.telemetryItem}>
                  <Text style={styles.telemetryVal}>{telemetry?.system_info?.uptime_seconds ? `${Math.floor(telemetry.system_info.uptime_seconds / 60)}m` : 'N/A'}</Text>
                  <Text style={styles.telemetryLbl}>Uptime</Text>
                </View>
              </View>
            </View>

            {/* Quick Desktop Controls */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Desktop Controls</Text>
              <View style={styles.controlGrid}>
                <TouchableOpacity style={styles.btnControl} onPress={() => runDesktopIntent('volume up')}>
                  <Ionicons name="volume-high" size={24} color="#8B5CF6" />
                  <Text style={styles.btnControlText}>Vol Up</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnControl} onPress={() => runDesktopIntent('volume down')}>
                  <Ionicons name="volume-low" size={24} color="#8B5CF6" />
                  <Text style={styles.btnControlText}>Vol Down</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnControl} onPress={() => runDesktopIntent('mute')}>
                  <Ionicons name="volume-mute" size={24} color="#EF4444" />
                  <Text style={styles.btnControlText}>Mute</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnControl} onPress={() => runDesktopIntent('show desktop')}>
                  <Ionicons name="desktop-outline" size={24} color="#10B981" />
                  <Text style={styles.btnControlText}>Desktop</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnControl} onPress={() => runDesktopIntent('lock computer')}>
                  <Ionicons name="lock-closed" size={24} color="#F59E0B" />
                  <Text style={styles.btnControlText}>Lock PC</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnControl} onPress={simulateVoiceDictation}>
                  <Ionicons name="mic-circle" size={24} color="#EC4899" />
                  <Text style={styles.btnControlText}>Dictate</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Remote Screen Capture */}
            <View style={styles.card}>
              <View style={styles.rowBetween}>
                <Text style={styles.cardTitle}>Live View (Screen Capture)</Text>
                <TouchableOpacity style={styles.btnSmall} onPress={captureScreenshot}>
                  {screenshotLoading ? <ActivityIndicator size="small" color="#fff" /> : <Text style={styles.btnSmallText}>Refresh</Text>}
                </TouchableOpacity>
              </View>
              {lastScreenshotUrl ? (
                <Image source={{ uri: lastScreenshotUrl }} style={styles.screenshotImage} resizeMode="contain" />
              ) : (
                <View style={styles.screenshotPlaceholder}>
                  <Ionicons name="image-outline" size={40} color="#475569" />
                  <Text style={styles.placeholderText}>No screenshot loaded.</Text>
                </View>
              )}
            </View>
          </ScrollView>
        );

      case 'chat':
        return (
          <View style={styles.tabContentContainer}>
            <ScrollView style={styles.chatScroll} contentContainerStyle={{ padding: 15 }}>
              {chatLog.map(item => (
                <View key={item.id} style={[styles.chatBubble, item.sender === 'user' ? styles.userBubble : styles.assistantBubble]}>
                  <Text style={styles.chatText}>{item.text}</Text>
                </View>
              ))}
            </ScrollView>
            <View style={styles.chatInputRow}>
              <TextInput
                style={styles.chatInput}
                placeholder="Ask Khushi..."
                placeholderTextColor="#64748B"
                value={chatMessage}
                onChangeText={setChatMessage}
              />
              <TouchableOpacity style={styles.btnSend} onPress={sendChatMessage}>
                <Ionicons name="send" size={20} color="#fff" />
              </TouchableOpacity>
            </View>
          </View>
        );

      case 'tasks':
        return (
          <ScrollView style={styles.scrollContainer} onLayout={() => { loadTasks(); loadGoals(); }}>
            {/* Task checklist */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Mobile Sync Tasks</Text>
              
              {/* Task list */}
              {Object.keys(tasks).length > 0 ? (
                Object.entries(tasks).map(([k, v]) => (
                  <View key={k} style={styles.taskItem}>
                    <View style={styles.flexRow}>
                      <Ionicons name="checkbox-outline" size={20} color="#10B981" />
                      <Text style={styles.taskText}>{k}: <Text style={{color: '#94A3B8'}}>{v?.value || v}</Text></Text>
                    </View>
                    <TouchableOpacity onPress={() => deleteTask(k)}>
                      <Ionicons name="trash-outline" size={18} color="#EF4444" />
                    </TouchableOpacity>
                  </View>
                ))
              ) : (
                <Text style={styles.placeholderText}>No tasks synced.</Text>
              )}

              {/* Add task form */}
              <View style={styles.addTaskForm}>
                <TextInput
                  style={styles.taskInput}
                  placeholder="Task Key (e.g. upsc_polity)"
                  placeholderTextColor="#64748B"
                  value={newTaskKey}
                  onChangeText={setNewTaskKey}
                />
                <TextInput
                  style={styles.taskInput}
                  placeholder="Task Description"
                  placeholderTextColor="#64748B"
                  value={newTaskVal}
                  onChangeText={setNewTaskVal}
                />
                <TouchableOpacity style={styles.btnSubmit} onPress={addTask}>
                  <Text style={styles.btnSubmitText}>Add Sync Task</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Goals list */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Desktop Active Goals</Text>
              {goals.agentic_goals.length > 0 || goals.companion_goals.length > 0 ? (
                <View>
                  {goals.agentic_goals.map((g, idx) => (
                    <View key={idx} style={styles.goalItem}>
                      <Ionicons name="flag-outline" size={16} color="#8B5CF6" />
                      <Text style={styles.goalText}>{g.name || g}</Text>
                    </View>
                  ))}
                  {goals.companion_goals.map((g, idx) => (
                    <View key={idx} style={styles.goalItem}>
                      <Ionicons name="ribbon-outline" size={16} color="#EC4899" />
                      <Text style={styles.goalText}>{g.payload?.value || g}</Text>
                    </View>
                  ))}
                </View>
              ) : (
                <Text style={styles.placeholderText}>No active planning goals.</Text>
              )}
            </View>

            {/* Clipboard sync */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Clipboard Synchronizer</Text>
              <TextInput
                style={styles.clipboardInput}
                multiline
                placeholder="Type or paste clipboard contents..."
                placeholderTextColor="#64748B"
                value={clipboardText}
                onChangeText={setClipboardText}
              />
              <View style={styles.rowBetween}>
                <TouchableOpacity style={styles.btnSubmitHalf} onPress={syncClipboardGet}>
                  <Text style={styles.btnSubmitText}>Pull Desktop</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnSubmitHalf} onPress={syncClipboardSet}>
                  <Text style={styles.btnSubmitText}>Push Desktop</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        );

      case 'media':
        return (
          <ScrollView style={styles.scrollContainer} onLayout={loadSharedFiles}>
            {/* Quick Upload Tools */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Quick Upload Controls</Text>
              <View style={styles.rowBetween}>
                <TouchableOpacity style={styles.btnSubmitHalf} onPress={simulateCameraUpload}>
                  <Ionicons name="camera" size={18} color="#fff" />
                  <Text style={styles.btnSubmitText}>Camera Photo</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnSubmitHalf} onPress={simulateScreenshotUpload}>
                  <Ionicons name="image" size={18} color="#fff" />
                  <Text style={styles.btnSubmitText}>Screenshot</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* File Transfer */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Shared File Storage</Text>
              <TextInput
                style={styles.taskInput}
                placeholder="Filename (e.g. notes.txt)"
                placeholderTextColor="#64748B"
                value={sharedFileName}
                onChangeText={setSharedFileName}
              />
              <TextInput
                style={styles.clipboardInput}
                multiline
                placeholder="File contents..."
                placeholderTextColor="#64748B"
                value={sharedFileContent}
                onChangeText={setSharedFileContent}
              />
              <TouchableOpacity style={styles.btnSubmit} onPress={uploadTextFile}>
                <Text style={styles.btnSubmitText}>Upload Shared File</Text>
              </TouchableOpacity>

              {/* Shared Files List */}
              <Text style={[styles.cardTitle, { marginTop: 20 }]}>Available Files on Desktop</Text>
              {filesList.length > 0 ? (
                filesList.map(name => (
                  <TouchableOpacity key={name} style={styles.fileItem} onPress={() => downloadSharedFile(name)}>
                    <Ionicons name="document-text-outline" size={18} color="#94A3B8" />
                    <Text style={styles.fileItemText}>{name}</Text>
                  </TouchableOpacity>
                ))
              ) : (
                <Text style={styles.placeholderText}>No shared files uploaded.</Text>
              )}

              {/* View Downloaded File */}
              {selectedFileContent && (
                <View style={styles.downloadedFileCard}>
                  <View style={styles.rowBetween}>
                    <Text style={styles.downloadedFileTitle}>{selectedFileContent.name}</Text>
                    <TouchableOpacity onPress={() => setSelectedFileContent(null)}>
                      <Ionicons name="close-circle-outline" size={20} color="#EF4444" />
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.downloadedFileBody}>{selectedFileContent.content}</Text>
                </View>
              )}
            </View>
          </ScrollView>
        );

      case 'events':
        return (
          <ScrollView style={styles.scrollContainer}>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Live Events & Notifications</Text>
              {eventsLog.map((ev, idx) => (
                <View key={idx} style={styles.eventItem}>
                  <View style={styles.rowBetween}>
                    <Text style={styles.eventTopic}>{ev.topic}</Text>
                    <Text style={styles.eventTime}>{ev.timestamp}</Text>
                  </View>
                  <Text style={styles.eventDetail}>{ev.detail}</Text>
                </View>
              ))}
            </View>
          </ScrollView>
        );

      default:
        return null;
    }
  }

  // Pairing screen if not authenticated
  if (!paired) {
    return (
      <SafeAreaView style={styles.pairContainer}>
        <StatusBar style="light" />
        <View style={styles.pairHeader}>
          <Text style={styles.pairTitle}>Khushi AI</Text>
          <Text style={styles.pairSubtitle}>Mobile Companion Client</Text>
        </View>

        <View style={styles.pairCard}>
          <Text style={styles.pairInputLabel}>Server LAN URL</Text>
          <TextInput
            style={styles.pairInput}
            value={serverUrl}
            onChangeText={setServerUrl}
            placeholder="http://192.168.x.x:8000"
            placeholderTextColor="#475569"
          />

          <Text style={styles.pairInputLabel}>Secure API Key</Text>
          <TextInput
            style={styles.pairInput}
            value={apiToken}
            onChangeText={setApiToken}
            placeholder="Paste secure API Key here"
            placeholderTextColor="#475569"
            secureTextEntry
          />

          <TouchableOpacity style={styles.btnPair} onPress={() => pairServer()} disabled={connecting}>
            {connecting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.btnPairText}>Pair and Connect</Text>
            )}
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Dashboard / Paired app layout
  return (
    <SafeAreaView style={styles.appContainer}>
      <StatusBar style="light" />
      {/* Top Header Bar */}
      <View style={styles.topHeader}>
        <View>
          <Text style={styles.topTitle}>{desktopName}</Text>
          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>Connected via LAN</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.btnDisconnect} onPress={disconnectServer}>
          <Text style={styles.btnDisconnectText}>Disconnect</Text>
        </TouchableOpacity>
      </View>

      {/* Main content body */}
      <View style={{ flex: 1 }}>
        {renderTabContent()}
      </View>

      {/* Bottom Navigation Bar */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={[styles.navItem, activeTab === 'dashboard' && styles.activeNavItem]} onPress={() => setActiveTab('dashboard')}>
          <Ionicons name="speedometer-outline" size={20} color={activeTab === 'dashboard' ? '#8B5CF6' : '#64748B'} />
          <Text style={[styles.navText, activeTab === 'dashboard' && styles.activeNavText]}>Controls</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.navItem, activeTab === 'chat' && styles.activeNavItem]} onPress={() => setActiveTab('chat')}>
          <Ionicons name="chatbubbles-outline" size={20} color={activeTab === 'chat' ? '#8B5CF6' : '#64748B'} />
          <Text style={[styles.navText, activeTab === 'chat' && styles.activeNavText]}>Chat</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.navItem, activeTab === 'tasks' && styles.activeNavItem]} onPress={() => setActiveTab('tasks')}>
          <Ionicons name="checkbox-outline" size={20} color={activeTab === 'tasks' ? '#8B5CF6' : '#64748B'} />
          <Text style={[styles.navText, activeTab === 'tasks' && styles.activeNavText]}>Tasks</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.navItem, activeTab === 'media' && styles.activeNavItem]} onPress={() => setActiveTab('media')}>
          <Ionicons name="cloud-upload-outline" size={20} color={activeTab === 'media' ? '#8B5CF6' : '#64748B'} />
          <Text style={[styles.navText, activeTab === 'media' && styles.activeNavText]}>Media</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.navItem, activeTab === 'events' && styles.activeNavItem]} onPress={() => setActiveTab('events')}>
          <Ionicons name="notifications-outline" size={20} color={activeTab === 'events' ? '#8B5CF6' : '#64748B'} />
          <Text style={[styles.navText, activeTab === 'events' && styles.activeNavText]}>Events</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  // Safe area wrappers
  pairContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
    justifyContent: 'center',
    padding: 20
  },
  appContainer: {
    flex: 1,
    backgroundColor: '#090D16'
  },
  scrollContainer: {
    flex: 1,
    padding: 15
  },
  tabContentContainer: {
    flex: 1
  },

  // Pairing View Styles
  pairHeader: {
    alignItems: 'center',
    marginBottom: 40
  },
  pairTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#8B5CF6',
    letterSpacing: 1
  },
  pairSubtitle: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 5
  },
  pairCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
    elevation: 4
  },
  pairInputLabel: {
    color: '#E2E8F0',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 6,
    textTransform: 'uppercase'
  },
  pairInput: {
    backgroundColor: '#0F172A',
    borderRadius: 6,
    padding: 10,
    color: '#fff',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)'
  },
  btnPair: {
    backgroundColor: '#8B5CF6',
    borderRadius: 6,
    padding: 12,
    alignItems: 'center',
    marginTop: 10
  },
  btnPairText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 15
  },

  // App Layout styles
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#161F30',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)'
  },
  topTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: 'bold'
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 3
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
    marginRight: 6
  },
  statusText: {
    color: '#10B981',
    fontSize: 10,
    fontWeight: 'bold'
  },
  btnDisconnect: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.2)',
    borderRadius: 4,
    paddingVertical: 4,
    paddingHorizontal: 8
  },
  btnDisconnectText: {
    color: '#EF4444',
    fontSize: 11,
    fontWeight: 'bold'
  },

  // Cards & Layout Elements
  card: {
    backgroundColor: '#111827',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.03)'
  },
  cardTitle: {
    color: '#E2E8F0',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 12
  },

  // Telemetry Grid
  telemetryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between'
  },
  telemetryItem: {
    width: '47%',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginBottom: 10
  },
  telemetryVal: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#38BDF8'
  },
  telemetryLbl: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 4
  },

  // Controls Grid
  controlGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between'
  },
  btnControl: {
    width: '30%',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginBottom: 10
  },
  btnControlText: {
    color: '#E2E8F0',
    fontSize: 10,
    fontWeight: 'bold',
    marginTop: 6
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  btnSmall: {
    backgroundColor: '#8B5CF6',
    borderRadius: 4,
    paddingVertical: 5,
    paddingHorizontal: 10
  },
  btnSmallText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold'
  },
  screenshotImage: {
    width: '100%',
    height: 180,
    borderRadius: 6,
    marginTop: 5,
    backgroundColor: '#000'
  },
  screenshotPlaceholder: {
    width: '100%',
    height: 180,
    borderRadius: 6,
    backgroundColor: '#1E293B',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 5
  },
  placeholderText: {
    color: '#64748B',
    fontSize: 12,
    marginTop: 5
  },

  // Chat Tab Styles
  chatScroll: {
    flex: 1,
    backgroundColor: '#0F172A'
  },
  chatBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#8B5CF6',
    borderBottomRightRadius: 2
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#334155',
    borderBottomLeftRadius: 2
  },
  chatText: {
    color: '#fff',
    fontSize: 14
  },
  chatInputRow: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#1E293B',
    alignItems: 'center'
  },
  chatInput: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
    color: '#fff',
    marginRight: 10,
    fontSize: 14
  },
  btnSend: {
    backgroundColor: '#8B5CF6',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center'
  },

  // Tasks Tab Styles
  taskItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 6,
    padding: 10,
    marginBottom: 8
  },
  flexRow: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  taskText: {
    color: '#E2E8F0',
    fontSize: 12,
    marginLeft: 8
  },
  addTaskForm: {
    marginTop: 15,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
    paddingTop: 15
  },
  taskInput: {
    backgroundColor: '#0F172A',
    borderRadius: 6,
    padding: 8,
    color: '#fff',
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
    fontSize: 12
  },
  btnSubmit: {
    backgroundColor: '#10B981',
    borderRadius: 6,
    padding: 10,
    alignItems: 'center'
  },
  btnSubmitText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
    marginLeft: 5
  },
  goalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 6,
    padding: 10,
    marginBottom: 6
  },
  goalText: {
    color: '#E2E8F0',
    fontSize: 12,
    marginLeft: 8
  },
  clipboardInput: {
    backgroundColor: '#0F172A',
    borderRadius: 6,
    padding: 8,
    color: '#fff',
    minHeight: 60,
    textAlignVertical: 'top',
    marginBottom: 10,
    fontSize: 12
  },
  btnSubmitHalf: {
    width: '48%',
    backgroundColor: '#8B5CF6',
    borderRadius: 6,
    padding: 10,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center'
  },

  // Media Tab Styles
  fileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    backgroundColor: '#1E293B',
    borderRadius: 6,
    marginBottom: 8
  },
  fileItemText: {
    color: '#E2E8F0',
    fontSize: 12,
    marginLeft: 8
  },
  downloadedFileCard: {
    marginTop: 15,
    backgroundColor: '#0F172A',
    borderRadius: 6,
    padding: 12,
    borderWidth: 1,
    borderColor: '#38BDF8'
  },
  downloadedFileTitle: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: 'bold'
  },
  downloadedFileBody: {
    color: '#E2E8F0',
    fontSize: 11,
    fontFamily: 'monospace',
    marginTop: 8
  },

  // Events Feed Styles
  eventItem: {
    backgroundColor: '#1E293B',
    borderRadius: 6,
    padding: 10,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#EC4899'
  },
  eventTopic: {
    color: '#F472B6',
    fontWeight: 'bold',
    fontSize: 10
  },
  eventTime: {
    color: '#64748B',
    fontSize: 9
  },
  eventDetail: {
    color: '#CBD5E1',
    fontSize: 11,
    marginTop: 4
  },

  // Bottom Navigation Bar
  bottomNav: {
    flexDirection: 'row',
    height: 60,
    backgroundColor: '#161F30',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
    justifyContent: 'space-around',
    alignItems: 'center'
  },
  navItem: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '20%'
  },
  activeNavItem: {
    // optional active item highlight
  },
  navText: {
    color: '#64748B',
    fontSize: 9,
    marginTop: 4
  },
  activeNavText: {
    color: '#8B5CF6',
    fontWeight: 'bold'
  }
});
