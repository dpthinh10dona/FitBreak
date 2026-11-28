import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import '../style/explainableAi.css';

const RagProvenanceDrawer = ({ chunks = [] }) => {
  const [expanded, setExpanded] = useState(false);

  if (!Array.isArray(chunks) || chunks.length === 0) return null;

  return (
    <div className="rag-provenance-wrapper">
      <button
        type="button"
        className="rag-provenance-toggle"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        <BookOpen size={13} />
        <span>Xem căn cứ &amp; Nguồn trích xuất ({chunks.length})</span>
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>

      {expanded && (
        <div className="rag-provenance-panel">
          {chunks.map((chunk, idx) => {
            const scorePct =
              typeof chunk.similarity_score === 'number'
                ? `${Math.round(chunk.similarity_score * 100)}% khớp`
                : null;
            return (
              <div key={idx} className="rag-chunk-card">
                <div className="rag-chunk-meta">
                  <span className="rag-chunk-title">
                    {chunk.doc_title || 'Tài liệu tham khảo'}
                  </span>
                  {scorePct && <span className="rag-chunk-score">{scorePct}</span>}
                </div>
                {chunk.section_or_page && (
                  <div className="rag-chunk-section">
                    Vị trí: {chunk.section_or_page}
                  </div>
                )}
                <p className="rag-chunk-text">{chunk.raw_text}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RagProvenanceDrawer;
