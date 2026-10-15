/**
 * NexCart — useCountUp Hook
 * Smooth count-up animation using requestAnimationFrame.
 * Animates from 0 to target over duration ms. Re-animates on target change.
 */

import { useState, useEffect, useRef } from 'react';

export default function useCountUp(target, duration = 1200) {
  const [currentValue, setCurrentValue] = useState(0);
  const rafRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    if (typeof target !== 'number' || isNaN(target)) {
      setCurrentValue(target);
      return;
    }

    startTimeRef.current = null;

    const animate = (timestamp) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic for smooth deceleration
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(eased * target);

      setCurrentValue(value);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [target, duration]);

  return currentValue;
}

// ✓ useCountUp.js complete
