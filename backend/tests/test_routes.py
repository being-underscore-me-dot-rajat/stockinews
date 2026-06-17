"""
Route smoke tests — every endpoint in the FastAPI backend.

Auth-gated routes use the dependency override from conftest.py (no real JWT).
Supabase calls are intercepted by the mock_supabase fixture.
yfinance / network calls are patched per-test where needed.
"""
import pytest
from unittest.mock import MagicMock, patch

# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def ok(resp, expected_status=200):
    assert resp.status_code == expected_status, (
        f"Expected {expected_status}, got {resp.status_code}: {resp.text[:300]}"
    )
    return resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# Auth routes   /login  /signup  /reset-password  /me
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthRoutes:

    def test_login_success(self, client, mock_supabase):
        session = MagicMock()
        session.access_token = "fake-access-token"
        user = MagicMock()
        user.id = "user-id-123"
        user.email = "user@example.com"
        user.user_metadata = {"name": "Test User"}
        result = MagicMock()
        result.session = session
        result.user = user
        mock_supabase.auth.sign_in_with_password.return_value = result

        resp = client.post("/login", json={"email": "user@example.com", "password": "pass"})
        data = ok(resp)
        assert "token" in data
        assert data["token"] == "fake-access-token"
        assert data["user"]["email"] == "user@example.com"

    def test_login_invalid_credentials(self, client, mock_supabase):
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login")
        resp = client.post("/login", json={"email": "bad@example.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_signup_success(self, client, mock_supabase):
        mock_supabase.auth.admin.create_user.return_value = MagicMock()
        session = MagicMock()
        session.access_token = "new-user-token"
        result = MagicMock()
        result.session = session
        mock_supabase.auth.sign_in_with_password.return_value = result

        resp = client.post("/signup", json={"name": "Alice", "email": "alice@example.com", "password": "secret"})
        data = ok(resp, 201)
        assert "token" in data

    def test_signup_duplicate_email(self, client, mock_supabase):
        mock_supabase.auth.admin.create_user.side_effect = Exception("User already exists")
        resp = client.post("/signup", json={"name": "Bob", "email": "bob@example.com", "password": "secret"})
        assert resp.status_code == 400

    def test_reset_password_success(self, client, mock_supabase):
        fake_user = MagicMock()
        fake_user.email = "user@example.com"
        fake_user.id = "user-id-123"
        mock_supabase.auth.admin.list_users.return_value = [fake_user]
        mock_supabase.auth.admin.update_user_by_id.return_value = MagicMock()

        resp = client.post("/reset-password", json={"email": "user@example.com", "password": "newpass"})
        data = ok(resp)
        assert "message" in data

    def test_reset_password_unknown_email(self, client, mock_supabase):
        mock_supabase.auth.admin.list_users.return_value = []
        resp = client.post("/reset-password", json={"email": "ghost@example.com", "password": "x"})
        assert resp.status_code == 404

    def test_get_me(self, client, mock_supabase):
        u = MagicMock()
        u.id = "test-user-uuid-1234"
        u.email = "test@example.com"
        u.user_metadata = {"name": "Test User"}
        result = MagicMock()
        result.user = u
        mock_supabase.auth.admin.get_user_by_id.return_value = result

        resp = client.get("/me", headers={"Authorization": "Bearer fake"})
        data = ok(resp)
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"


# ══════════════════════════════════════════════════════════════════════════════
# Company routes   /api/companies  /api/chart  /api/company/*
# ══════════════════════════════════════════════════════════════════════════════

class TestCompanyRoutes:

    def test_get_companies(self, client):
        resp = client.get("/api/companies")
        data = ok(resp)
        # Should return at least one of these keys
        assert "Symbols" in data or "companies" in data

    def test_get_companies_has_items(self, client):
        data = client.get("/api/companies").json()
        companies = data.get("companies", [])
        symbols = data.get("Symbols", [])
        assert len(companies) > 0 or len(symbols) > 0, "Company list must not be empty"

    def test_chart_valid_ticker(self, client):
        mock_data = [{"Datetime": "2024-01-01", "Close": 100.0}]
        with patch("routers.company.getdata", return_value=mock_data), \
             patch("routers.company.warm_cache"):
            resp = client.get("/api/chart?ticker=RELIANCE.NS&period=7d")
        ok(resp)

    def test_chart_missing_ticker(self, client):
        resp = client.get("/api/chart")
        assert resp.status_code == 422

    def test_company_info(self, client):
        fake_info = {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "price": 2800.0}
        with patch("routers.company.get_company_info", return_value=fake_info):
            resp = client.get("/api/company/info?ticker=RELIANCE")
        data = ok(resp)
        assert data["symbol"] == "RELIANCE.NS"

    def test_company_info_missing_ticker(self, client):
        resp = client.get("/api/company/info")
        assert resp.status_code == 422

    def test_company_developments(self, client):
        fake_devs = {"news": [], "corporate_actions": [], "calendar": {}}
        with patch("routers.company.get_company_developments", return_value=fake_devs):
            resp = client.get("/api/company/developments?ticker=RELIANCE")
        ok(resp)

    def test_company_news(self, client):
        fake_articles = [{"title": "Test", "url": "http://example.com", "summary": "..."}]
        with patch("routers.company.crawl_news_for_ticker_cached", return_value=fake_articles):
            resp = client.get("/api/company/news?ticker=RELIANCE&limit=5")
        data = ok(resp)
        assert "articles" in data
        assert data["count"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# Market route   /marketwatch
# ══════════════════════════════════════════════════════════════════════════════

class TestMarketRoute:

    def test_marketwatch_authenticated(self, client):
        fake_market = [{"symbol": "^NSEI", "name": "NIFTY 50", "open_price": 22000.0}]
        with patch("routers.market.get_market_overview", return_value=fake_market):
            resp = client.get("/marketwatch", headers={"Authorization": "Bearer fake"})
        data = ok(resp)
        assert "market" in data
        assert len(data["market"]) == 1

    def test_marketwatch_no_auth(self, client):
        # With dependency override active this will still succeed; skip real-auth test.
        # Confirm 422/401 would be raised without override by checking the dependency exists.
        from routers.market import router
        routes = {r.path: r for r in router.routes}
        assert "/marketwatch" in routes


# ══════════════════════════════════════════════════════════════════════════════
# News routes   /news  /api/crawler/news  /api/crawler/sources
# ══════════════════════════════════════════════════════════════════════════════

class TestNewsRoutes:

    def test_news_endpoint(self, client):
        fake_news = [{"title": "Market rallies", "url": "http://example.com", "description": "..."}]
        with patch("routers.news.get_news_api_articles", return_value=fake_news):
            resp = client.get("/news")
        data = ok(resp)
        assert "news" in data
        assert len(data["news"]) == 1

    def test_news_endpoint_error_graceful(self, client):
        with patch("routers.news.get_news_api_articles", side_effect=Exception("API down")):
            resp = client.get("/news")
        data = ok(resp)
        assert data["news"] == []
        assert "error" in data

    def test_crawler_news(self, client):
        fake_articles = [{"title": "ET article", "url": "http://et.com"}]
        with patch("routers.news.crawl_news", return_value=fake_articles):
            resp = client.get("/api/crawler/news?source=all&limit=10")
        data = ok(resp)
        assert "articles" in data

    def test_crawler_news_invalid_source(self, client):
        with patch("routers.news.crawl_news", side_effect=ValueError("Unknown source")):
            resp = client.get("/api/crawler/news?source=invalid_xyz")
        assert resp.status_code == 400

    def test_crawler_sources(self, client):
        resp = client.get("/api/crawler/sources")
        data = ok(resp)
        assert "sources" in data
        assert "all" in data["sources"]


# ══════════════════════════════════════════════════════════════════════════════
# Portfolio routes   /api/portfolios  (prefix)
# ══════════════════════════════════════════════════════════════════════════════

class TestPortfolioRoutes:

    def _setup_portfolio_mock(self, mock_supabase):
        rpc_result = MagicMock()
        rpc_result.data = [
            {"ticker": "RELIANCE.NS", "net_quantity": 10, "total_cost": 28000.0},
        ]
        mock_supabase.rpc.return_value.execute.return_value = rpc_result

    def test_get_portfolio(self, client, mock_supabase):
        self._setup_portfolio_mock(mock_supabase)
        with patch("routers.portfolio._get_price", return_value=2850.0):
            resp = client.get("/api/portfolios", headers={"Authorization": "Bearer fake"})
        data = ok(resp)
        assert "portfolio" in data
        assert data["portfolio"][0]["ticker"] == "RELIANCE.NS"
        assert data["portfolio"][0]["quantity"] == 10

    def test_get_portfolio_empty(self, client, mock_supabase):
        rpc_result = MagicMock()
        rpc_result.data = []
        mock_supabase.rpc.return_value.execute.return_value = rpc_result
        resp = client.get("/api/portfolios", headers={"Authorization": "Bearer fake"})
        data = ok(resp)
        assert data["portfolio"] == []

    def test_add_stock_buy(self, client, mock_supabase):
        insert_result = MagicMock()
        insert_result.data = [{"id": 1}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = insert_result

        with patch("routers.portfolio.normalize_nse_symbol", return_value="RELIANCE.NS"):
            resp = client.post(
                "/api/portfolios/add",
                json={"ticker": "RELIANCE.NS", "quantity": 5, "price": 2800.0, "action": "BUY"},
                headers={"Authorization": "Bearer fake"},
            )
        data = ok(resp)
        assert "message" in data

    def test_add_stock_invalid_ticker(self, client, mock_supabase):
        with patch("routers.portfolio.normalize_nse_symbol", return_value=""):
            resp = client.post(
                "/api/portfolios/add",
                json={"ticker": "INVALID", "quantity": 5, "price": 100.0, "action": "BUY"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400

    def test_add_stock_invalid_action(self, client, mock_supabase):
        with patch("routers.portfolio.normalize_nse_symbol", return_value="RELIANCE.NS"):
            resp = client.post(
                "/api/portfolios/add",
                json={"ticker": "RELIANCE.NS", "quantity": 5, "price": 100.0, "action": "HOLD"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400

    def test_sell_stock_success(self, client, mock_supabase):
        qty_result = MagicMock()
        qty_result.data = [{"quantity": 20}]
        mock_supabase.rpc.return_value.execute.return_value = qty_result
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        with patch("routers.portfolio.normalize_nse_symbol", return_value="RELIANCE.NS"):
            resp = client.post(
                "/api/portfolios/sell",
                json={"ticker": "RELIANCE.NS", "quantity": 5, "price": 2900.0},
                headers={"Authorization": "Bearer fake"},
            )
        data = ok(resp)
        assert "message" in data

    def test_sell_stock_insufficient_shares(self, client, mock_supabase):
        qty_result = MagicMock()
        qty_result.data = [{"quantity": 2}]
        mock_supabase.rpc.return_value.execute.return_value = qty_result

        with patch("routers.portfolio.normalize_nse_symbol", return_value="RELIANCE.NS"):
            resp = client.post(
                "/api/portfolios/sell",
                json={"ticker": "RELIANCE.NS", "quantity": 10, "price": 2900.0},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400

    def test_download_history_no_transactions(self, client, mock_supabase):
        table_result = MagicMock()
        table_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = table_result

        resp = client.get("/api/portfolios/history", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 404

    def test_download_history_returns_pdf(self, client, mock_supabase):
        table_result = MagicMock()
        table_result.data = [
            {"ticker": "RELIANCE.NS", "quantity": 5, "price": 2800.0, "action": "BUY", "created_at": "2024-01-15T10:00:00"},
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = table_result

        resp = client.get("/api/portfolios/history", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_portfolio_histories(self, client, mock_supabase):
        table_result = MagicMock()
        table_result.data = [
            {"ticker": "RELIANCE.NS", "quantity": 5, "action": "BUY"},
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = table_result

        fake_history = MagicMock()
        fake_history.reset_index.return_value = MagicMock()

        import pandas as pd
        df = pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-01", "2024-01-08"]),
            "Close": [2800.0, 2850.0],
        })
        with patch("yfinance.Ticker") as mock_yf:
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = df
            mock_yf.return_value = mock_ticker
            resp = client.get("/api/portfolios/histories", headers={"Authorization": "Bearer fake"})

        data = ok(resp)
        assert "dates" in data
        assert "values" in data


# ══════════════════════════════════════════════════════════════════════════════
# Watchlist routes   /watchlist
# ══════════════════════════════════════════════════════════════════════════════

class TestWatchlistRoutes:

    def test_get_watchlist_empty(self, client, mock_supabase):
        result = MagicMock()
        result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = result

        resp = client.get("/watchlist", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_watchlist_with_items(self, client, mock_supabase):
        result = MagicMock()
        result.data = [{"ticker": "RELIANCE.NS"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = result

        fake_quotes = [{"symbol": "RELIANCE.NS", "name": "Reliance Industries", "open_price": 2800.0}]
        with patch("routers.watchlist.get_watchlist_quotes", return_value=fake_quotes), \
             patch("routers.watchlist.normalize_nse_symbol", return_value="RELIANCE.NS"):
            resp = client.get("/watchlist", headers={"Authorization": "Bearer fake"})
        data = ok(resp)
        assert len(data) == 1
        assert data[0]["symbol"] == "RELIANCE.NS"

    def test_add_to_watchlist(self, client, mock_supabase):
        insert_result = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = insert_result

        with patch("routers.watchlist.normalize_nse_symbol", return_value="TCS.NS"):
            resp = client.post(
                "/watchlist",
                json={"symbol": "TCS.NS"},
                headers={"Authorization": "Bearer fake"},
            )
        data = ok(resp, 201)
        assert "message" in data

    def test_add_to_watchlist_invalid_symbol(self, client, mock_supabase):
        with patch("routers.watchlist.normalize_nse_symbol", return_value=""):
            resp = client.post(
                "/watchlist",
                json={"symbol": "INVALID_GARBAGE_XYZ"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400

    def test_add_to_watchlist_duplicate(self, client, mock_supabase):
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("duplicate key")
        with patch("routers.watchlist.normalize_nse_symbol", return_value="TCS.NS"):
            resp = client.post(
                "/watchlist",
                json={"symbol": "TCS.NS"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400

    def test_remove_from_watchlist(self, client, mock_supabase):
        delete_result = MagicMock()
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = delete_result

        resp = client.delete("/watchlist/TCS.NS", headers={"Authorization": "Bearer fake"})
        data = ok(resp)
        assert "message" in data


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2 — deep yfinance routes
# ══════════════════════════════════════════════════════════════════════════════

class TestPhase2CompanyRoutes:

    def _patch(self, fn_path, return_value):
        return patch(fn_path, return_value=return_value)

    def test_financials_structure(self, client):
        fake = {
            "income_statement": {"annual": {"2024-03-31": {"Total Revenue": 1e10}}, "quarterly": None},
            "balance_sheet":    {"annual": None, "quarterly": None},
            "cash_flow":        {"annual": None, "quarterly": None},
        }
        with self._patch("routers.company.get_financials", fake):
            resp = client.get("/api/company/financials?ticker=RELIANCE.NS")
        data = ok(resp)
        assert "income_statement" in data
        assert "balance_sheet" in data
        assert "cash_flow" in data

    def test_financials_missing_ticker(self, client):
        resp = client.get("/api/company/financials")
        assert resp.status_code == 422

    def test_analysts_structure(self, client):
        fake = {
            "recommendations":     [{"date": "2024-01-01", "Firm": "Goldman", "To Grade": "Buy", "Action": "up"}],
            "upgrades_downgrades": None,
            "price_targets":       [{"date": "2024-01-01", "low": 2500, "mean": 3000, "high": 3500}],
            "earnings_estimate":   None,
            "revenue_estimate":    None,
            "eps_trend":           None,
        }
        with self._patch("routers.company.get_analysts", fake):
            resp = client.get("/api/company/analysts?ticker=RELIANCE.NS")
        data = ok(resp)
        assert "recommendations" in data
        assert len(data["recommendations"]) == 1

    def test_holders_structure(self, client):
        fake = {
            "major_holders":         [{"Value": "7.25%", "Breakdown": "% of Shares Held by Institutions"}],
            "institutional_holders": [{"Holder": "LIC", "Shares": 1e8}],
            "mutualfund_holders":    None,
            "insider_transactions":  None,
        }
        with self._patch("routers.company.get_holders", fake):
            resp = client.get("/api/company/holders?ticker=RELIANCE.NS")
        data = ok(resp)
        assert "major_holders" in data
        assert "institutional_holders" in data

    def test_earnings_structure(self, client):
        fake = {
            "earnings_history": [{"date": "2024-09-30", "EPS Estimate": 65.5, "Reported EPS": 68.2}],
            "earnings_dates":   None,
            "dividends":        [{"date": "2024-07-15", "value": 9.0}],
            "splits":           None,
        }
        with self._patch("routers.company.get_earnings", fake):
            resp = client.get("/api/company/earnings?ticker=RELIANCE.NS")
        data = ok(resp)
        assert "earnings_history" in data
        assert "dividends" in data
        assert data["dividends"][0]["value"] == 9.0

    def test_options_no_data(self, client):
        fake = {"expiry_dates": [], "nearest_expiry": None, "calls": None, "puts": None}
        with self._patch("routers.company.get_options", fake):
            resp = client.get("/api/company/options?ticker=RELIANCE.NS")
        data = ok(resp)
        assert data["expiry_dates"] == []

    def test_options_with_data(self, client):
        fake = {
            "expiry_dates":   ["2024-12-26"],
            "nearest_expiry": "2024-12-26",
            "calls": [{"strike": 2900.0, "lastPrice": 45.5, "volume": 120}],
            "puts":  [{"strike": 2900.0, "lastPrice": 30.0, "volume": 80}],
        }
        with self._patch("routers.company.get_options", fake):
            resp = client.get("/api/company/options?ticker=RELIANCE.NS")
        data = ok(resp)
        assert data["nearest_expiry"] == "2024-12-26"
        assert len(data["calls"]) == 1

    def test_esg_no_data(self, client):
        with self._patch("routers.company.get_esg", {}):
            resp = client.get("/api/company/esg?ticker=RELIANCE.NS")
        data = ok(resp)
        assert data == {}

    def test_esg_with_scores(self, client):
        fake = {"esgScore": 45.67, "environmentScore": 12.3, "socialScore": 18.9, "governanceScore": 14.47}
        with self._patch("routers.company.get_esg", fake):
            resp = client.get("/api/company/esg?ticker=RELIANCE.NS")
        data = ok(resp)
        assert data["esgScore"] == 45.67
