import React, { useEffect, useRef, useState } from 'react';
import './Dropdown.css';
import { API_BASE } from '../../lib/api';

function Dropdown({ onSelect, resetTrigger }) {
    const [searchTerm, setSearchTerm]   = useState('');
    const [results, setResults]         = useState([]);
    const [loading, setLoading]         = useState(false);
    const debounceRef                   = useRef(null);

    useEffect(() => {
        setSearchTerm('');
        setResults([]);
    }, [resetTrigger]);

    const handleInputChange = (e) => {
        const val = e.target.value;
        setSearchTerm(val);

        clearTimeout(debounceRef.current);
        if (val.trim().length < 2) {
            setResults([]);
            return;
        }

        debounceRef.current = setTimeout(async () => {
            setLoading(true);
            try {
                const res = await fetch(
                    `${API_BASE}/api/companies/search?q=${encodeURIComponent(val.trim())}`
                );
                const data = await res.json();
                setResults(data.results || []);
            } catch {
                setResults([]);
            } finally {
                setLoading(false);
            }
        }, 300);
    };

    const handleSelect = (company) => {
        setSearchTerm(company.display);
        setResults([]);
        if (onSelect) onSelect(company.nse_symbol);
    };

    return (
        <div className="dropdown-root">
            <div className="search-bar-container">
                <input
                    type="text"
                    value={searchTerm}
                    onChange={handleInputChange}
                    placeholder="Search company or ticker (e.g. Reliance, TCS)…"
                    className="search-bar-input"
                    autoComplete="off"
                />
                {loading && (
                    <div className="dropdown-loading">Searching…</div>
                )}
                {!loading && results.length > 0 && (
                    <ul
                        className="suggestions-list"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        {results.map((company, index) => (
                            <li
                                key={company.nse_symbol || index}
                                onClick={() => handleSelect(company)}
                                className="suggestion-item"
                            >
                                <span className="suggestion-symbol">{company.symbol}</span>
                                <span className="suggestion-name">{company.name}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default Dropdown;
