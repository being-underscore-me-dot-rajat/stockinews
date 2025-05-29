import React, { useEffect, useState } from 'react'
import './Dropdown.css'

function Dropdown() {
    const [companies, setCompanies] = useState("--Select--");
    const [loading, setLoading] = useState(true); 
    const [searchTerm, setSearchTerm] = useState("");
    const [filteredCompanies, setFilteredCompanies] = useState([]);


    // useEffect to fetch companies when the component is first loaded
    useEffect(() => {
        fetch('http://127.0.0.1:5000/api/companies')
            .then(response => response.json()) // Parsing the JSON response
            .then(data => {
                setCompanies(data.Symbols || []); // Safely set companies data or an empty array
                setLoading(false); // Update loading state when data is fetched
            })
            .catch(error => {
                console.error('Error fetching companies:', error); // Handling errors
                setLoading(false); // Ensure loading state is updated on error
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
        setFilteredCompanies([]);  // Hide suggestions after selection
        if (onSelect) onSelect(company);
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <div className='container'>
            <div className="search-bar-container">
                {/* Search Input */}
                <input
                    type="text"
                    value={searchTerm}
                    onChange={handleInputChange}
                    placeholder="Search companies..."
                    className="search-bar-input"
                />

                {/* Suggestions List */}
                {filteredCompanies.length > 0 && (
                    <ul className="suggestions-list">
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

export default Dropdown
