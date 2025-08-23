import { Link } from "react-router";
import { useState, useEffect, useRef } from "react";
import type { Route } from "./+types/game";

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Game - Snare Drum Challenge" },
		{ name: "description", content: "Hit the snare drum as fast as you can!" },
	];
}

type GameStatus = "countdown" | "playing" | "ended";

interface HitMessage {
	type: "hit";
	timestamp: number;
	hit_number: number;
	rms_value: number;
	threshold: number;
}

interface ConnectedMessage {
	type: "connected";
	timestamp: number;
	message: string;
}

const GAME_DURATION = 30; // seconds
const COUNTDOWN_DURATION = 3; // seconds
const WEBSOCKET_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8765";

export default function Game() {
	const [gameStatus, setGameStatus] = useState<GameStatus>("countdown");
	const [score, setScore] = useState(0);
	const [countdown, setCountdown] = useState(COUNTDOWN_DURATION);
	const [timeRemaining, setTimeRemaining] = useState(GAME_DURATION);
	const [hitRate, setHitRate] = useState(0);
	const [bestCombo, setBestCombo] = useState(0);
	const [currentCombo, setCurrentCombo] = useState(0);
	const [isConnected, setIsConnected] = useState(false);
	const [connectionError, setConnectionError] = useState<string | null>(null);
	const [drumAnimation, setDrumAnimation] = useState(false);

	const wsRef = useRef<WebSocket | null>(null);
	const gameTimerRef = useRef<number | null>(null);
	const countdownTimerRef = useRef<number | null>(null);
	const lastHitTimeRef = useRef<number>(0);
	const hitTimestampsRef = useRef<number[]>([]);
	const gameStatusRef = useRef<GameStatus>("countdown");

	// Calculate hit rate based on recent hits
	const calculateHitRate = () => {
		const now = Date.now();
		const recentHits = hitTimestampsRef.current.filter(
			(timestamp) => now - timestamp < 5000, // Last 5 seconds
		);
		const rate = recentHits.length / 5;
		setHitRate(Math.round(rate * 10) / 10);
	};

	// Handle WebSocket connection - connect once when component mounts
	useEffect(() => {
		// Connect to WebSocket
		try {
			const ws = new WebSocket(WEBSOCKET_URL);
			wsRef.current = ws;

			ws.onopen = () => {
				setIsConnected(true);
				setConnectionError(null);
				console.log("Connected to detector");
			};

			ws.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data) as HitMessage | ConnectedMessage;

					if (data.type === "connected") {
						console.log("Detector ready:", data.message);
					} else if (
						data.type === "hit" &&
						gameStatusRef.current === "playing"
					) {
						// Handle hit
						setScore((prev) => prev + 1);

						// Update combo
						const now = Date.now();
						if (now - lastHitTimeRef.current < 2000) {
							// Within 2 seconds
							setCurrentCombo((prev) => {
								const newCombo = prev + 1;
								setBestCombo((current) => Math.max(current, newCombo));
								return newCombo;
							});
						} else {
							setCurrentCombo(1);
						}
						lastHitTimeRef.current = now;

						// Track hit for rate calculation
						hitTimestampsRef.current.push(now);
						calculateHitRate();

						// Trigger drum animation
						setDrumAnimation(true);
						setTimeout(() => setDrumAnimation(false), 200);
					}
				} catch (err) {
					console.error("Failed to parse message:", err);
				}
			};

			ws.onerror = (error) => {
				console.error("WebSocket error:", error);
				setConnectionError("Failed to connect to detector");
				setIsConnected(false);
			};

			ws.onclose = () => {
				setIsConnected(false);
				console.log("Disconnected from detector");
			};
		} catch (err) {
			setConnectionError("Failed to connect to detector");
			console.error("WebSocket connection failed:", err);
		}

		return () => {
			// Cleanup WebSocket on unmount
			if (wsRef.current) {
				wsRef.current.close();
				wsRef.current = null;
			}
		};
	}, []); // Empty dependency array - connect once on mount

	// Start countdown when game status changes to countdown
	useEffect(() => {
		if (gameStatus === "countdown") {
			// Reset countdown to initial value
			setCountdown(COUNTDOWN_DURATION);

			countdownTimerRef.current = window.setInterval(() => {
				setCountdown((prev) => {
					if (prev <= 1) {
						// Start the game
						if (countdownTimerRef.current) {
							clearInterval(countdownTimerRef.current);
						}
						setGameStatus("playing");
						return 0;
					}
					return prev - 1;
				});
			}, 1000);
		}

		return () => {
			if (countdownTimerRef.current) {
				clearInterval(countdownTimerRef.current);
				countdownTimerRef.current = null;
			}
		};
	}, [gameStatus]);

	// Update gameStatusRef when gameStatus changes
	useEffect(() => {
		gameStatusRef.current = gameStatus;
	}, [gameStatus]);

	// Game timer
	useEffect(() => {
		if (gameStatus === "playing") {
			gameTimerRef.current = window.setInterval(() => {
				setTimeRemaining((prev) => {
					if (prev <= 0.1) {
						// End the game
						if (gameTimerRef.current) {
							clearInterval(gameTimerRef.current);
						}
						setGameStatus("ended");
						return 0;
					}
					return prev - 0.1;
				});

				// Update hit rate periodically
				calculateHitRate();
			}, 100); // Update every 100ms for smooth timer

			return () => {
				if (gameTimerRef.current) {
					clearInterval(gameTimerRef.current);
				}
			};
		}
	}, [gameStatus]);

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			if (wsRef.current) {
				wsRef.current.close();
			}
			if (gameTimerRef.current) {
				clearInterval(gameTimerRef.current);
			}
			if (countdownTimerRef.current) {
				clearInterval(countdownTimerRef.current);
			}
		};
	}, []);

	const getCountdownText = () => {
		switch (countdown) {
			case 3:
				return "Get ready...";
			case 2:
				return "Set...";
			case 1:
				return "Go!";
			default:
				return "Starting...";
		}
	};

	const playAgain = () => {
		// Reset all state
		setScore(0);
		setTimeRemaining(GAME_DURATION);
		setHitRate(0);
		setBestCombo(0);
		setCurrentCombo(0);
		hitTimestampsRef.current = [];
		lastHitTimeRef.current = 0;
		// Set game status to countdown last - this will trigger the countdown timer
		setGameStatus("countdown");
	};

	return (
		<div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4">
			<div className="max-w-4xl mx-auto text-center">
				{/* Connection Status */}
				{connectionError && (
					<div className="mb-4 p-4 bg-red-900/50 border border-red-500 text-red-300">
						⚠️ {connectionError}
					</div>
				)}

				{/* Game Header */}
				<div className="mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">
						Snare Drum Challenge
					</h1>
					<div className="flex justify-center items-center space-x-8 text-2xl">
						<div className="flat-card px-6 py-3">
							<span className="text-zinc-400">Time:</span>
							<span
								className={`font-mono ml-2 ${timeRemaining < 5 ? "text-red-400" : "text-green-400"}`}
							>
								{timeRemaining.toFixed(1)}s
							</span>
						</div>
						<div className="flat-card px-6 py-3">
							<span className="text-zinc-400">Score:</span>
							<span
								className={`text-green-400 font-mono ml-2 transition-all ${drumAnimation ? "scale-125" : ""}`}
							>
								{score}
							</span>
						</div>
					</div>
				</div>

				{/* Drum Visual */}
				<div className="mb-12">
					<div
						className={`w-80 h-80 mx-auto bg-red-600 border-4 border-red-500 flex items-center justify-center transition-transform ${
							drumAnimation ? "scale-110" : ""
						}`}
					>
						<span className="text-8xl select-none">🥁</span>
					</div>
				</div>

				{/* Game State Display */}
				{gameStatus === "countdown" && (
					<div className="mb-8 flat-card p-8">
						<div className="text-6xl font-bold text-red-400 mb-4">
							{countdown}
						</div>
						<div className="text-xl text-zinc-300">{getCountdownText()}</div>
						<div className="text-sm text-zinc-500 mt-2">
							Game starts in {countdown} seconds. Prepare your drumsticks!
						</div>
					</div>
				)}

				{gameStatus === "playing" && (
					<div className="mb-8">
						<div className="text-zinc-400 text-lg mb-4">
							Hit your physical snare drum to score points!
						</div>
						{currentCombo > 1 && (
							<div className="text-2xl text-yellow-400 font-bold animate-pulse">
								🔥 Combo x{currentCombo}!
							</div>
						)}
					</div>
				)}

				{gameStatus === "ended" && (
					<div className="mb-8 flat-card p-8">
						<div className="text-3xl font-bold text-white mb-4">Game Over!</div>
						<div className="text-5xl text-green-400 font-bold mb-2">
							{score}
						</div>
						<div className="text-xl text-zinc-300 mb-4">Total Hits</div>
						<div className="text-zinc-400 space-y-2">
							<div>Average: {(score / GAME_DURATION).toFixed(1)} hits/sec</div>
							<div>Best Combo: {bestCombo}</div>
						</div>
						<div className="mt-6 space-y-3">
							<button
								type="button"
								onClick={playAgain}
								className="flat-button-primary w-full"
							>
								Play Again
							</button>
							<Link to="/" className="flat-button block">
								Back to Home
							</Link>
						</div>
					</div>
				)}

				{/* Cancel/Actions */}
				{gameStatus !== "ended" && (
					<div className="flex justify-center">
						<Link to="/" className="flat-button">
							Cancel Game
						</Link>
					</div>
				)}
			</div>

			{/* Stats Overlay */}
			{gameStatus === "playing" && (
				<div className="fixed bottom-4 right-4 flat-card p-4">
					<div className="text-zinc-400 text-sm space-y-1">
						<div className="flex items-center gap-2">
							<span
								className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"}`}
							></span>
							{isConnected ? "Connected" : "Disconnected"}
						</div>
						<div>
							Hit Rate: <span className="text-white">{hitRate} hits/sec</span>
						</div>
						<div>
							Best Combo: <span className="text-yellow-400">{bestCombo}</span>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
