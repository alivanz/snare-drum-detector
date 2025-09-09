module.exports = {
  apps: [
    {
      name: "drum-detector",
      script: "main.py",
      args: "-d 2 -w",
      interpreter: "/home/orangepi/micromamba/envs/audio/bin/python",
    },
  ],
};