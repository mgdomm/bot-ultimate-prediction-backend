import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Ultimate Predictor",
    short_name: "UP",
    description: "Picks premium y parleys, con scoreboard en vivo.",
    start_url: "/",
    display: "standalone",
    background_color: "#0F172A",
    theme_color: "#0F172A",
    lang: "es",
    icons: [
      {
        src: "/icon.png",
        sizes: "2048x2048",
        type: "image/png",
      },
    ],
  };
}
