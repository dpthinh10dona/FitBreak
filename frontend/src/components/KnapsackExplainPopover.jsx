import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import '../style/explainableAi.css';

const KnapsackExplainPopover = ({ reason }) => {
  const [open, setOpen] = useState(false);

  if (!reason) return null;

  return (
    <span
      className="knapsack-explain-anchor"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="knapsack-explain-btn"
        aria-label="Giải thích lựa chọn bài tập"
        aria-expanded={open}
        onClick={(e) => {
          e.stopPropagation();
          setOpen((prev) => !prev);
        }}
      >
        <HelpCircle size={13} />
      </button>

      {open && (
        <div className="knapsack-explain-popover" role="tooltip">
          <span className="knapsack-explain-badge">
            Quyết định bởi thuật toán 0/1 Knapsack
          </span>
          <div>{reason}</div>
        </div>
      )}
    </span>
  );
};

export default KnapsackExplainPopover;
