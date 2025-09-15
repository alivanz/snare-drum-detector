import type { RouteConfig } from "@react-router/dev/routes";
import { index, route } from "@react-router/dev/routes";

export default [
	index("routes/home.tsx"),
	route("/game", "routes/game.tsx"),
	route("/score", "routes/score.tsx"),
	route("/leaderboard", "routes/leaderboard.tsx"),
	route("/settings", "routes/settings.tsx"),
	route("/locations", "routes/locations.tsx"),
] satisfies RouteConfig;
