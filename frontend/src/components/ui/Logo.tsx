/** Pictogramme Opsora : anneau dégradé bleu→violet (bulle/repère) + O blanc. */
export function Logo({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-label="Opsora">
      <defs>
        <linearGradient id="opsora-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#38BDF8" />
          <stop offset="1" stopColor="#8B5CF6" />
        </linearGradient>
      </defs>
      <circle
        cx="50" cy="44" r="33" fill="none" stroke="url(#opsora-grad)"
        strokeWidth="13" strokeLinecap="round"
        strokeDasharray="178.3 29" strokeDashoffset="-66.2"
      />
      <path
        fill="url(#opsora-grad)"
        d="M62 72c7 7 7 16 -3 25c2 -9 -2 -15 -9 -17c4 -1 9 -4 12 -8Z"
      />
      <circle cx="50" cy="44" r="14" fill="none" stroke="currentColor" strokeWidth="10" className="text-white" />
    </svg>
  );
}
