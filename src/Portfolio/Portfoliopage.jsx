import React, { useEffect, useState } from 'react';
import './portfoliopage.css'; // Make sure to define styles here
import { color } from 'chart.js/helpers';
import Dropdown from '../home/dropdown/Dropdown';
import Chartgen from './chartgen';
import Navbar from '../home/navbar/Navbar'

function Portfoliopage() {
  const [portfolio, setPortfolio] = useState([]);
  const [formData, setFormData] = useState({ ticker: '', quantity: '', price: '' });
  const [showAddForm, setShowAddForm] = useState(false);
  const [sellForms, setSellForms] = useState({});
  const [message, setMessage] = useState('');
  const token = localStorage.getItem('token');

  const fetchPortfolio = () => {
    fetch('http://localhost:5000/api/portfolio', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => res.json())
      .then(data => {
        if (data.portfolio) setPortfolio(data.portfolio);
        else setMessage(data.error || 'Failed to load portfolio');
      })
      .catch(() => setMessage('Error loading portfolio'));
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const handleAdd = (e) => {
    e.preventDefault();
    fetch('http://localhost:5000/api/portfolio/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ...formData, action: 'BUY' }),
    })
      .then(res => res.json())
      .then(data => {
        setMessage(data.message || data.error);
        if (data.message) {
          setFormData({ ticker: '', quantity: '', price: '' });
          setShowAddForm(false);
          fetchPortfolio(); // ✅ Refresh portfolio
        }
      })
      .catch(() => setMessage('Error adding stock'));
  };

  const handleSell = (ticker, quantity, price) => {
    fetch('http://localhost:5000/api/portfolio/sell', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ticker, quantity, price }),
    })
      .then(res => res.json())
      .then(data => {
        setMessage(data.message || data.error);
        if (data.message) {
          setSellForms({ ...sellForms, [ticker]: false });
          fetchPortfolio(); // ✅ Refresh portfolio
        }
      })
      .catch(() => setMessage('Error selling stock'));
  };

  return (
    <>
    <Navbar />
    <div className="portfolio-container" style={{ color: 'white' }}>
      <h2 className="section-title">📊 My Portfolio</h2>
      {message && <p className="message">{message}</p>}

      <table className="portfolio-table">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Quantity</th>
            <th>Buy Price</th>
            <th>Current Price</th>
            <th>Profit/Loss</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {portfolio.map((item, index) => {
            const profit = ((item.current_price - item.avg_price) * item.quantity).toFixed(2);
            const showSell = sellForms[item.ticker];

            return (
              <React.Fragment key={index}>
                <tr>
                  <td>{item.ticker}</td>
                  <td>{item.quantity}</td>
                  <td>{item.avg_price}</td>
                  <td>{item.current_price}</td>
                  <td style={{ color: profit >= 0 ? 'green' : 'red' }}>{profit}</td>
                  <td>
                    <button onClick={() =>
                      setSellForms({ ...sellForms, [item.ticker]: !showSell })
                    }>
                      {showSell ? 'Cancel' : 'Sell'}
                    </button>
                  </td>
                </tr>
                {showSell && (
                  <tr>
                    <td colSpan="6">
                      <form onSubmit={(e) => {
                        e.preventDefault();
                        const quantity = e.target.quantity.value;
                        const price = e.target.price.value;
                        handleSell(item.ticker, quantity, price);
                      }}>
                        <input name="quantity" type="number" placeholder="Quantity" required />
                        <input name="price" type="number" step="0.01" placeholder="Sell Price" required />
                        <button type="submit">Confirm Sell</button>
                      </form>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>

      {/* Add Stock Section */}
      {!showAddForm ? (
        <button onClick={() => setShowAddForm(true)}>➕ Add Stock</button>
      ) : (
        <div className="form-section">
          <h3>Add Stock</h3>
          <form onSubmit={handleAdd}>
  <Dropdown onSelect={(company) => setFormData({ ...formData, ticker: company })} />

  <input
    type="number"
    placeholder="Quantity"
    value={formData.quantity}
    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
    required
  />
  <input
    type="number"
    step="0.01"
    placeholder="Buy Price"
    value={formData.price}
    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
    required
  />

  <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
    <button type="submit">Add</button>
    <button type="button" onClick={() => setShowAddForm(false)}>Cancel</button>
  </div>
</form>
        </div>
      )}
      <div className="form-section">
  <h3>Download Transaction History</h3>
  <button
    onClick={() => {
      fetch('http://localhost:5000/api/portfolio/history', {
        headers: {
          Authorization: `Bearer ${token}`,
        }
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to download PDF');
        }
        return response.blob(); // Convert to binary
      })
      .then(blob => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'portfolio_history.pdf');
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
      })
      .catch(err => {
        setMessage(err.message);
      });
    }}
  >
    📥 Download PDF
  </button>
</div>
    <Chartgen portfolio={portfolio} />
    
    </div>
    </>
  );

}

export default Portfoliopage;
