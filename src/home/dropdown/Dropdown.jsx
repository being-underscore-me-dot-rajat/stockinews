import React, { useEffect, useState } from 'react';
import './Dropdown.css';

function Dropdown({ onSelect, resetTrigger, token }) {
  const [companies, setCompanies] = useState([]); // Fix: Initialize as array
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredCompanies, setFilteredCompanies] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/companies')
      .then(response => response.json())
      .then(data => {
        setCompanies(data.Symbols || []);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching companies:', error);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = companies.filter(company =>
        company.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredCompanies(filtered);
    } else {
      setFilteredCompanies([]);
    }
  }, [searchTerm, companies]);

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSelect = (company) => {
    setSearchTerm(company);
    setFilteredCompanies([]);
    if (onSelect) onSelect(company);
  };
  useEffect(() => {
    setSearchTerm("");
    setFilteredCompanies([]);
  }, [resetTrigger]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className='container'>
      <div className="search-bar-container">
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          placeholder="Search companies..."
          className="search-bar-input"
        />
        {filteredCompanies.length > 0 && (
          <ul className="suggestions-list" onMouseDown={(e) => e.stopPropagation()}>
  {filteredCompanies.map((company, index) => (
    <li
      key={index}
      onClick={() => handleSelect(company)}
      className="suggestion-item"
    >
      {company}
    </li>
  ))}
</ul>
        )}
      </div>
    </div>
  );
}

export default Dropdown;
