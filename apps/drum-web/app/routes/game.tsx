import { parseWithZod } from "@conform-to/zod/v4";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, redirect, useFetcher } from "react-router";
import { z } from "zod";
import type { Route } from "./+types/game";

const scoreSchema = z.object({
	score: z.coerce.number().min(0),
	combo: z.coerce.number().min(0),
	duration: z.coerce.number().min(0),
});

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Game - Snare Drum Challenge" },
		{ name: "description", content: "Hit the snare drum as fast as you can!" },
	];
}

export async function loader({ context }: Route.LoaderArgs) {
	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	// Get current settings to ensure location is set
	const currentSettings = await stub.getSettings();

	if (!currentSettings || !currentSettings.locationId) {
		return redirect("/settings");
	}

	return { locationId: currentSettings.locationId };
}

export async function action({ request, context }: Route.ActionArgs) {
	const formData = await request.formData();
	const submission = parseWithZod(formData, { schema: scoreSchema });

	if (submission.status !== "success") {
		return submission.reply({ formErrors: ["Invalid score data"] });
	}

	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	// Get current settings for location
	const currentSettings = await stub.getSettings();

	if (!currentSettings || !currentSettings.locationId) {
		return submission.reply({ formErrors: ["No location set"] });
	}

	// Add the score
	await stub.addScore({
		locationId: currentSettings.locationId,
		score: submission.value.score,
		combo: submission.value.combo,
		duration: submission.value.duration * 1000, // Convert to milliseconds
	});

	return submission.reply({ resetForm: true });
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
	const [scoreSubmitted, setScoreSubmitted] = useState(false);

	const fetcher = useFetcher();
	const wsRef = useRef<WebSocket | null>(null);
	const gameTimerRef = useRef<number | null>(null);
	const countdownTimerRef = useRef<number | null>(null);
	const lastHitTimeRef = useRef<number>(0);
	const hitTimestampsRef = useRef<number[]>([]);
	const gameStatusRef = useRef<GameStatus>("countdown");
	const gameStartTimeRef = useRef<number>(0);

	// Calculate hit rate based on recent hits
	const calculateHitRate = useCallback(() => {
		const now = Date.now();
		const recentHits = hitTimestampsRef.current.filter(
			(timestamp) => now - timestamp < 5000, // Last 5 seconds
		);
		const rate = recentHits.length / 5;
		setHitRate(Math.round(rate * 10) / 10);
	}, []);

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
						gameStartTimeRef.current = Date.now(); // Record game start time
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
	}, [gameStatus, calculateHitRate]);

	// Submit score when game ends
	useEffect(() => {
		if (gameStatus === "ended" && !scoreSubmitted && score > 0) {
			const gameDuration = (Date.now() - gameStartTimeRef.current) / 1000; // Convert to seconds

			const formData = new FormData();
			formData.append("score", score.toString());
			formData.append("combo", bestCombo.toString());
			formData.append("duration", gameDuration.toString());

			fetcher.submit(formData, { method: "post" });
			setScoreSubmitted(true);
		}
	}, [gameStatus, score, bestCombo, scoreSubmitted, fetcher]);

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
		setScoreSubmitted(false);
		hitTimestampsRef.current = [];
		lastHitTimeRef.current = 0;
		// Set game status to countdown last - this will trigger the countdown timer
		setGameStatus("countdown");
	};

	// Format score with decimal separator
	const formatScore = (num: number) => {
		return num.toLocaleString("en-US", {
			minimumFractionDigits: 3,
			maximumFractionDigits: 3,
		});
	};

	// Format time as MM:SS
	const formatTime = (seconds: number) => {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
	};

	return (
		<div
			className="min-h-screen flex flex-col items-center justify-center p-4 relative"
			style={{
				backgroundImage: "url(/background.jpg)",
				backgroundSize: "cover",
				backgroundPosition: "center",
				backgroundRepeat: "no-repeat",
			}}
		>
			{/* Connection Error */}
			{connectionError && (
				<div className="absolute top-4 left-1/2 transform -translate-x-1/2 p-4 bg-red-900/80 border border-red-500 text-red-300 rounded-lg backdrop-blur-sm">
					⚠️ {connectionError}
				</div>
			)}

			{/* Main Game UI - Always visible when playing or countdown */}
			{(gameStatus === "playing" || gameStatus === "countdown") && (
				<div className="flex flex-col items-center">
					{/* Combo Display */}
					{currentCombo > 1 && (
						<div className="mb-8">
							<h2 className="text-5xl font-bold text-white uppercase tracking-wider italic">
								COMBO <span className="text-6xl">{currentCombo}x</span>
							</h2>
						</div>
					)}

					{/* Timer Badge */}
					<div
						className="mb-8 px-12 py-4 rounded-lg"
						style={{
							background:
								"linear-gradient(180deg, #E0E0E0 0%, #9E9E9E 50%, #757575 100%)",
							boxShadow:
								"0 4px 6px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5)",
						}}
					>
						<div className="flex items-center gap-4">
							<span className="text-3xl">⏱</span>
							<span className="text-4xl font-bold text-black">
								{formatTime(timeRemaining)}
							</span>
						</div>
					</div>

					{/* Score Card */}
					<div className="bg-black/60 backdrop-blur-sm rounded-lg p-8 border-2 border-white/30 min-w-[400px]">
						<h3 className="text-xl text-white/80 uppercase tracking-widest mb-4 text-center">
							YOUR SCORE
						</h3>
						<div className="text-7xl font-bold text-white text-center">
							{formatScore(score)}
						</div>
					</div>

					{/* Motivational Text */}
					<div className="mt-8">
						<p className="text-2xl text-white uppercase tracking-wider font-semibold">
							KEEP HITTING THE SNARE!
						</p>
					</div>
				</div>
			)}

			{/* Countdown Overlay */}
			{gameStatus === "countdown" && (
				<div className="fixed inset-0 bg-black/75 flex flex-col items-center justify-center z-50">
					<div className="text-center">
						<div className="text-[200px] font-bold text-white mb-8 leading-none">
							{countdown}
						</div>
						<p className="text-5xl text-white uppercase tracking-wider font-bold italic">
							{getCountdownText()}
						</p>
					</div>
				</div>
			)}

			{gameStatus === "ended" && (
				<div className="text-center">
					<div className="bg-black/60 backdrop-blur-sm rounded-2xl p-12 border border-white/20 max-w-md">
						<div className="text-4xl font-bold text-white mb-6 uppercase tracking-wider">
							Game Over!
						</div>
						<div className="text-6xl text-white font-bold mb-2">
							{formatScore(score)}
						</div>
						<div className="text-xl text-white/80 mb-6 uppercase">
							Total Hits
						</div>
						<div className="text-white/60 space-y-2 mb-8">
							<div>Average: {(score / GAME_DURATION).toFixed(1)} hits/sec</div>
							<div>Best Combo: {bestCombo}x</div>
						</div>
						<div className="space-y-3">
							<button
								type="button"
								onClick={playAgain}
								className="w-full px-6 py-3 bg-white text-black font-bold uppercase tracking-wider rounded hover:bg-gray-200 transition-colors"
							>
								Play Again
							</button>
							<Link
								to="/"
								className="block w-full px-6 py-3 bg-transparent border-2 border-white text-white font-bold uppercase tracking-wider rounded hover:bg-white/10 transition-colors"
							>
								Back to Home
							</Link>
						</div>
					</div>
				</div>
			)}

			{/* Cancel Button */}
			{gameStatus !== "ended" && (
				<div className="absolute bottom-8 right-8">
					<Link
						to="/"
						className="text-white text-xl font-bold uppercase tracking-wider hover:text-white/80 transition-colors underline"
					>
						Cancel
					</Link>
				</div>
			)}

			{/* Connection Status Indicator */}
			{gameStatus === "playing" && (
				<div className="absolute top-4 right-4">
					<div className="flex items-center gap-2 bg-black/40 backdrop-blur-sm rounded-full px-4 py-2">
						<span
							className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"} animate-pulse`}
						></span>
						<span className="text-white text-sm">
							{isConnected ? "Connected" : "Disconnected"}
						</span>
					</div>
				</div>
			)}
		</div>
	);
}
