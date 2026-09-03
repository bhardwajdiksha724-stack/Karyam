import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: "#14171F",       // page background
        surface: "#1C202B",    // cards, panels, sidebar
        border: "#2A2F3D",     // hairline dividers
        text: {
          DEFAULT: "#EDEFF4",  // primary text
          muted: "#8B92A6",    // secondary text
        },
        accent: "#4F8CFF",     // primary actions, links, focus rings
        status: {
          todo: "#8B92A6",
          progress: "#F5A623",
          done: "#34C77B",
          high: "#FF5C5C",
        },
      },
      fontFamily: {
        display: ["Sora", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
    plugins: [typography],
};