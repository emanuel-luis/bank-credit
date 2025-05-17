import React, { useState, useEffect, useRef } from 'react';
import './Carousel.css';

export default function Carousel({ items, visibleCount = 3, autoSlideInterval = 7500 }) {
  const total = items.length;
  const [index, setIndex] = useState(0);
  const [transition, setTransition] = useState(true);
  const intervalRef = useRef();

  // Avanço automático
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      handleNext();
    }, autoSlideInterval);
    return () => clearInterval(intervalRef.current);
  }, [autoSlideInterval, total]);

  // Avanço manual
  const handlePrev = () => {
    setTransition(true);
    setIndex(i => (i - 1 + total) % total);
  };
  const handleNext = () => {
    setTransition(true);
    setIndex(i => (i + 1) % total);
  };

  // Gera os itens visíveis (loop infinito)
  const getVisibleItems = () => {
    const arr = [];
    for (let i = 0; i < visibleCount; i++) {
      const idx = (index + i) % total;
      arr.push(
        <div
          className={"carousel-content carousel-slide"}
          key={idx}
          style={{
            minWidth: 360,
            maxWidth: 360,
            opacity: 1,
            transform: `translateX(0)`,
            transition: 'transform 0.7s cubic-bezier(.4,0,.2,1), opacity 0.5s',
          }}
        >
          {items[idx]}
        </div>
      );
    }
    return arr;
  };

  return (
    <div className="carousel multi-carousel" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', overflow: 'visible', display: 'flex', justifyContent: 'center' }}>
      <div className="carousel-track carousel-track-static" style={{ width: 'auto', display: 'flex', justifyContent: 'center', alignItems: 'stretch', gap: '1.5rem', overflow: 'visible' }}>
        {getVisibleItems()}
      </div>
    </div>
  );
}
