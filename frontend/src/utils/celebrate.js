import confetti from "canvas-confetti";

/** A quick celebratory burst — used for real achievements (completing a
 * task, hitting a weekly hours milestone), not routine form saves. */
export function celebrate() {
  confetti({
    particleCount: 120,
    spread: 75,
    origin: { y: 0.6 },
    colors: ["#4F8CFF", "#B14FFF", "#34C77B"],
  });
}