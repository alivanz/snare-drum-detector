module.exports = {
	apps: [
		{
			name: "drum-web",
			script: "pnpm",
			args: "dev",
			interpreter: "none", // tells PM2 not to use node, just run the command directly
		},
	],
};
