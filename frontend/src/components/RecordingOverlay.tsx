import React, { useState, useRef, useEffect } from 'react';
import { 
    MicrophoneIcon, 
    StopIcon, 
    PauseIcon, 
    PlayIcon,
    ArrowPathIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import api from '../api';

interface Props {
    meetingId: number;
    meetingType: 'Regular' | 'BR';
    meetingMode?: string;
    onComplete?: () => void;
}

const RecordingOverlay: React.FC<Props> = ({ meetingId, meetingType, meetingMode, onComplete }) => {
    const isOnline = meetingMode === 'Online';

    const [isRecording, setIsRecording] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [time, setTime] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
    const [signalLevel, setSignalLevel] = useState(0);
    
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<number | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animationFrameRef = useRef<number | null>(null);

    // Get devices on mount
    useEffect(() => {
        const getDevices = async () => {
            try {
                // Request temporary access to get labels
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const devs = await navigator.mediaDevices.enumerateDevices();
                const audioDevs = devs.filter(d => d.kind === 'audioinput');
                setDevices(audioDevs);
                if (audioDevs.length > 0) setSelectedDeviceId(audioDevs[0].deviceId);
                
                // Stop the temp stream
                stream.getTracks().forEach(t => t.stop());
            } catch (err) {
                console.error('Error fetching devices:', err);
            }
        };
        getDevices();
    }, []);

    // Timer Logic
    useEffect(() => {
        let timer: number | null = null;
        
        if (isRecording && !isPaused) {
            timer = window.setInterval(() => setTime(prev => prev + 1), 1000);
        } else {
            if (timer) clearInterval(timer);
        }
        
        return () => { 
            if (timer) clearInterval(timer); 
        };
    }, [isRecording, isPaused]);

    const formatTime = (seconds: number) => {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const startRecording = async () => {
        try {
            let stream: MediaStream;
            let displayStream: MediaStream | null = null;
            
            if (isOnline) {
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                
                if (isMobile) {
                    // Mobile & Tablet: System audio capture is impossible natively in browser
                    toast.error("Mobile Browsers cannot record internal audio directly due to OS security. Please use Desktop for system audio capture.", { duration: 6000 });
                    return;
                }

                // Desktop: Online meeting -> Request Screen Share with System Audio Mandatory
                toast.loading("Click 'Share', select 'Entire Screen' or 'Tab', and CHECK 'Share Audio'!!", { duration: 6000 });
                
                try {
                    displayStream = await navigator.mediaDevices.getDisplayMedia({
                        video: true, 
                        audio: {
                            echoCancellation: false, // Turn off for cleaner system sound
                            noiseSuppression: false,
                            autoGainControl: false
                        }
                    });
                    
                    const audioTracks = displayStream.getAudioTracks();
                    if (audioTracks.length === 0) {
                        displayStream.getTracks().forEach(t => t.stop());
                        toast.error("Capture Failed: System Audio checkmark was NOT checked!");
                        return;
                    }
                    
                    // We only take the system audio track (Mic is NOT used)
                    stream = new MediaStream([audioTracks[0]]);
                    
                    const videoTrack = displayStream.getVideoTracks()[0];
                    if (videoTrack) videoTrack.onended = () => stopRecording();
                } catch (e) {
                    console.error("System audio capture error:", e);
                    toast.error("System audio capture cancelled or failed.");
                    return;
                }
            } else {
                // Offline meeting -> Capture MICROPHONE
                stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: { 
                        deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
                    } 
                });
            }
            
            const options = { mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 128000 };
            mediaRecorderRef.current = new MediaRecorder(stream, options);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunksRef.current.push(e.data);
                }
            };

            mediaRecorderRef.current.onstop = async () => {
                const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                
                // Stop all tracks to release hardware and remove sharing indicator
                stream.getTracks().forEach(t => t.stop());
                if (displayStream) displayStream.getTracks().forEach(t => t.stop());

                await finalizeMeeting(blob);
            };

            // Signal monitor setup (works for both Mic and System sound perfectly!)
            audioContextRef.current = new AudioContext();
            analyserRef.current = audioContextRef.current.createAnalyser();
            const source = audioContextRef.current.createMediaStreamSource(stream);
            source.connect(analyserRef.current);
            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            
            const check = () => {
                if (analyserRef.current) {
                    analyserRef.current.getByteFrequencyData(dataArray);
                    const avg = dataArray.reduce((a,b) => a+b) / dataArray.length;
                    setSignalLevel(avg);
                    animationFrameRef.current = requestAnimationFrame(check);
                }
            };
            check();

            mediaRecorderRef.current.start(1000);
            setIsRecording(true);
            setTime(0);
            toast.success(isOnline ? "System audio recording started" : "Recording System Active");
        } catch (err) {
            console.error('Start Error:', err);
            if (isOnline) {
                toast.error("Screen Share cancelled or Audio not allowed.");
            } else {
                toast.error("Microphone Error: Please check device selection.");
            }
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            setIsRecording(false);
        }
    };

    const finalizeMeeting = async (blob: Blob) => {
        setIsProcessing(true);
        const formData = new FormData();
        formData.append('meeting_id', meetingId.toString());
        formData.append('meeting_type', meetingType);
        formData.append('audio_file', blob, 'meeting_recording.webm');
        try {
            await api.post('/recording/process', formData);
            toast.success("Intelligence report is generating...");
            if (onComplete) onComplete();
        } catch (e) {
            toast.error("Upload failed.");
        } finally {
            setIsProcessing(false);
        }
    };

    if (isProcessing) return (
        <div className="p-4 bg-brand-50 dark:bg-brand-500/5 rounded-2xl border border-brand-200 dark:border-brand-500/20 flex items-center gap-3">
            <ArrowPathIcon className="w-5 h-5 text-brand-500 animate-spin shrink-0" />
            <div>
                <p className="text-[13px] font-bold text-brand-700 dark:text-brand-400">Uploading Recording...</p>
                <p className="text-[11px] text-slate-500">AI pipeline will start automatically. Check progress below.</p>
            </div>
        </div>
    );

    if (!isRecording) return (
        <div className="p-4 bg-slate-50 dark:bg-white/5 rounded-3xl border border-slate-200 dark:border-white/10 flex flex-col gap-4">
            {!isOnline && (
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center">
                        <MicrophoneIcon className="w-5 h-5 text-brand-500" />
                    </div>
                    <div className="flex-1">
                        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Speaker Source</label>
                        <select 
                            value={selectedDeviceId}
                            onChange={(e) => setSelectedDeviceId(e.target.value)}
                            className="w-full bg-transparent text-sm font-bold outline-none dark:text-white"
                        >
                            {devices.map(d => <option key={d.deviceId} value={d.deviceId}>{d.label || 'Default Audio Device'}</option>)}
                        </select>
                    </div>
                </div>
            )}
            <button onClick={startRecording} className="w-full py-4 bg-brand-600 text-white rounded-2xl font-bold hover:bg-brand-700 shadow-xl shadow-brand-500/20 active:scale-95 transition-all">
                {isOnline ? "Start System Recording" : "Start Intelligence Capture"}
            </button>
        </div>
    );

    return (
        <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-[100] w-full max-w-xl px-4">
            <div className="bg-white/95 dark:bg-[#1e2533]/95 backdrop-blur-xl p-5 rounded-3xl shadow-2xl border border-brand-500/20 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className="w-12 h-12 rounded-2xl bg-brand-500/20 flex items-center justify-center">
                            <MicrophoneIcon className="w-6 h-6 text-brand-500" />
                        </div>
                        <div className="absolute -bottom-1 left-0 w-full h-1.5 bg-slate-100 dark:bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-brand-500 transition-all duration-75" style={{ width: `${Math.min(100, signalLevel * 3)}%` }}></div>
                        </div>
                    </div>
                    <div>
                        <div className="text-lg font-black dark:text-white leading-none">{formatTime(time)}</div>
                        <div className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${signalLevel > 2 ? 'text-green-500' : 'text-slate-400'}`}>
                            {signalLevel > 2 ? 'Voice Signal Detected' : 'No Sound Detected...'}
                        </div>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button onClick={() => setIsPaused(!isPaused)} className="p-3 bg-slate-100 dark:bg-white/5 rounded-2xl">
                        {isPaused ? <PlayIcon className="w-6 h-6" /> : <PauseIcon className="w-6 h-6 text-brand-500" />}
                    </button>
                    <button onClick={stopRecording} className="px-6 py-3 bg-red-500 text-white rounded-2xl font-bold shadow-lg hover:bg-red-600">Finish</button>
                </div>
            </div>
        </div>
    );
};

export default RecordingOverlay;
