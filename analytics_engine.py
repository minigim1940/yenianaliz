"""
Phase 8.E: Advanced Analytics & Reporting - Analytics Engine
Real-time analytics, trend detection, performance analysis
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from collections import defaultdict
import statistics

class AnalyticsEngine:
    """Advanced analytics engine for API metrics and usage analysis"""
    
    def __init__(self, metrics_db: str = "api_metrics.db"):
        self.db_path = Path(metrics_db)
        self.ensure_tables()
    
    def ensure_tables(self):
        """Ensure analytics tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Analytics cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            conn.commit()
    
    def _check_table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,)).fetchone()
                return result is not None
        except Exception:
            return False
    
    def _get_demo_data(self) -> Dict:
        """Return demo data when request_logs table doesn't exist"""
        return {
            "total_requests": 1250,
            "success_requests": 1187,
            "error_requests": 63,
            "success_rate": 94.96,
            "error_rate": 5.04,
            "avg_response_time": 145.3,
            "max_response_time": 2340,
            "min_response_time": 12,
            "percentiles": {
                "p50": 98,
                "p75": 156,
                "p90": 234,
                "p95": 412,
                "p99": 1245
            },
            "top_endpoints": [
                {"endpoint": "/api/predict", "requests": 450, "avg_time": 187},
                {"endpoint": "/api/system-status", "requests": 320, "avg_time": 45},
                {"endpoint": "/api/analytics/usage-summary", "requests": 180, "avg_time": 234},
                {"endpoint": "/cache-stats", "requests": 150, "avg_time": 23},
                {"endpoint": "/api/v2/auth/token", "requests": 150, "avg_time": 67}
            ],
            "note": "Demo data - request_logs table not available"
        }
    
    def get_usage_summary(self, hours: int = 24) -> Dict:
        """Get API usage summary for specified hours"""
        # Check if request_logs table exists (changed from api_metrics)
        if not self._check_table_exists('request_logs'):
            demo_data = self._get_demo_data()
            demo_data['hours'] = hours
            return demo_data
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = datetime.now() - timedelta(hours=hours)
                
                # Total requests
                result = conn.execute("""
                    SELECT COUNT(*) as total_requests,
                           AVG(response_time) as avg_response_time,
                           MAX(response_time) as max_response_time,
                           MIN(response_time) as min_response_time
                    FROM request_logs
                    WHERE timestamp > ?
                """, (cutoff,)).fetchone()
                
                total_requests = result['total_requests'] if result else 0
                
                # Success rate
                success = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM request_logs
                    WHERE timestamp > ? AND status_code < 400
                """, (cutoff,)).fetchone()
                
                success_count = success['count'] if success else 0
                success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
                
                # Error rate
                errors = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM request_logs
                    WHERE timestamp > ? AND status_code >= 400
                """, (cutoff,)).fetchone()
                
                error_count = errors['count'] if errors else 0
                error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
                
                # Top endpoints
                top_endpoints = conn.execute("""
                    SELECT endpoint, COUNT(*) as count
                    FROM request_logs
                    WHERE timestamp > ?
                    GROUP BY endpoint
                    ORDER BY count DESC
                    LIMIT 10
                """, (cutoff,)).fetchall()
                
                # Response time percentiles
                response_times = conn.execute("""
                    SELECT response_time
                    FROM request_logs
                    WHERE timestamp > ? AND response_time IS NOT NULL
                    ORDER BY response_time
                """, (cutoff,)).fetchall()
                
                times = [r['response_time'] for r in response_times]
                percentiles = self._calculate_percentiles(times) if times else {}
                
                return {
                    "period": f"{hours}h",
                    "total_requests": total_requests,
                    "success_count": success_count,
                    "error_count": error_count,
                    "success_rate": round(success_rate, 2),
                    "error_rate": round(error_rate, 2),
                    "avg_response_time": round(result['avg_response_time'], 3) if result and result['avg_response_time'] else 0,
                    "max_response_time": round(result['max_response_time'], 3) if result and result['max_response_time'] else 0,
                    "min_response_time": round(result['min_response_time'], 3) if result and result['min_response_time'] else 0,
                    "percentiles": percentiles,
                    "top_endpoints": [
                        {"endpoint": row['endpoint'], "count": row['count']}
                        for row in top_endpoints
                    ]
                }
        except Exception as e:
            return {"error": str(e)}
    
    def get_endpoint_analytics(self, endpoint: str, hours: int = 24) -> Dict:
        """Get detailed analytics for a specific endpoint"""
        # Check if request_logs table exists
        if not self._check_table_exists('request_logs'):
            return {
                "endpoint": endpoint,
                "hours": hours,
                "total_requests": 150,
                "avg_response_time": 187,
                "success_rate": 95.3,
                "note": "Demo data - request_logs table not available"
            }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = datetime.now() - timedelta(hours=hours)
                
                # Basic stats
                result = conn.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        AVG(response_time) as avg_response_time,
                        MAX(response_time) as max_response_time,
                        MIN(response_time) as min_response_time,
                        AVG(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) * 100 as success_rate
                    FROM request_logs
                    WHERE endpoint = ? AND timestamp > ?
                """, (endpoint, cutoff)).fetchone()
                
                if not result or result['total_requests'] == 0:
                    return {"error": "No data found for this endpoint"}
                
                # Status code distribution
                status_codes = conn.execute("""
                    SELECT status_code, COUNT(*) as count
                    FROM request_logs
                    WHERE endpoint = ? AND timestamp > ?
                    GROUP BY status_code
                    ORDER BY count DESC
                """, (endpoint, cutoff)).fetchall()
                
                # Hourly distribution
                hourly = conn.execute("""
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        COUNT(*) as count,
                        AVG(response_time) as avg_time
                    FROM request_logs
                    WHERE endpoint = ? AND timestamp > ?
                    GROUP BY hour
                    ORDER BY hour
                """, (endpoint, cutoff)).fetchall()
                
                # Response times
                response_times = conn.execute("""
                    SELECT response_time
                    FROM request_logs
                    WHERE endpoint = ? AND timestamp > ? AND response_time IS NOT NULL
                    ORDER BY response_time
                """, (endpoint, cutoff)).fetchall()
                
                times = [r['response_time'] for r in response_times]
                percentiles = self._calculate_percentiles(times) if times else {}
                
                return {
                    "endpoint": endpoint,
                    "period": f"{hours}h",
                    "total_requests": result['total_requests'],
                    "success_rate": round(result['success_rate'], 2),
                    "avg_response_time": round(result['avg_response_time'], 3),
                    "max_response_time": round(result['max_response_time'], 3),
                    "min_response_time": round(result['min_response_time'], 3),
                    "percentiles": percentiles,
                    "status_codes": [
                        {"code": row['status_code'], "count": row['count']}
                        for row in status_codes
                    ],
                    "hourly_distribution": [
                        {
                            "hour": row['hour'],
                            "count": row['count'],
                            "avg_time": round(row['avg_time'], 3) if row['avg_time'] else 0
                        }
                        for row in hourly
                    ]
                }
        except Exception as e:
            return {"error": str(e)}
    
    def detect_anomalies(self, hours: int = 24, threshold: float = 2.0) -> Dict:
        """Detect anomalies in API usage and performance"""
        # Check if request_logs table exists
        if not self._check_table_exists('request_logs'):
            return {
                "anomalies": [],
                "total_checked": 0,
                "note": "Demo mode - request_logs table not available"
            }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = datetime.now() - timedelta(hours=hours)
                
                # Get all response times
                response_times = conn.execute("""
                    SELECT endpoint, response_time, timestamp
                    FROM request_logs
                    WHERE timestamp > ? AND response_time IS NOT NULL
                """, (cutoff,)).fetchall()
                
                if not response_times:
                    return {"anomalies": [], "total_checked": 0}
                
                # Group by endpoint
                endpoint_times = defaultdict(list)
                for row in response_times:
                    endpoint_times[row['endpoint']].append({
                        'time': row['response_time'],
                        'timestamp': row['timestamp']
                    })
                
                anomalies = []
                
                # Check each endpoint for anomalies
                for endpoint, times in endpoint_times.items():
                    if len(times) < 10:  # Need enough data
                        continue
                    
                    response_values = [t['time'] for t in times]
                    mean = statistics.mean(response_values)
                    
                    if len(response_values) > 1:
                        stdev = statistics.stdev(response_values)
                        
                        # Find outliers (beyond threshold standard deviations)
                        for time_data in times:
                            z_score = abs((time_data['time'] - mean) / stdev) if stdev > 0 else 0
                            
                            if z_score > threshold:
                                anomalies.append({
                                    "endpoint": endpoint,
                                    "response_time": round(time_data['time'], 3),
                                    "expected_avg": round(mean, 3),
                                    "z_score": round(z_score, 2),
                                    "timestamp": time_data['timestamp'],
                                    "severity": "high" if z_score > 3 else "medium"
                                })
                
                # Sort by z_score
                anomalies.sort(key=lambda x: x['z_score'], reverse=True)
                
                return {
                    "anomalies": anomalies[:50],  # Top 50
                    "total_anomalies": len(anomalies),
                    "total_checked": len(response_times),
                    "threshold": threshold,
                    "period": f"{hours}h"
                }
        except Exception as e:
            return {"error": str(e)}
    
    def get_trend_analysis(self, metric: str = "requests", days: int = 7) -> Dict:
        """Analyze trends over time"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = datetime.now() - timedelta(days=days)
                
                if metric == "requests":
                    # Daily request count trend
                    data = conn.execute("""
                        SELECT 
                            DATE(timestamp) as date,
                            COUNT(*) as count
                        FROM request_logs
                        WHERE timestamp > ?
                        GROUP BY date
                        ORDER BY date
                    """, (cutoff,)).fetchall()
                    
                elif metric == "response_time":
                    # Daily avg response time trend
                    data = conn.execute("""
                        SELECT 
                            DATE(timestamp) as date,
                            AVG(response_time) as value
                        FROM request_logs
                        WHERE timestamp > ? AND response_time IS NOT NULL
                        GROUP BY date
                        ORDER BY date
                    """, (cutoff,)).fetchall()
                    
                elif metric == "error_rate":
                    # Daily error rate trend
                    data = conn.execute("""
                        SELECT 
                            DATE(timestamp) as date,
                            AVG(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 100 as value
                        FROM request_logs
                        WHERE timestamp > ?
                        GROUP BY date
                        ORDER BY date
                    """, (cutoff,)).fetchall()
                else:
                    return {"error": "Invalid metric"}
                
                if not data:
                    return {"trend": [], "analysis": "No data available"}
                
                # Calculate trend
                values = [row['count'] if metric == "requests" else row['value'] for row in data]
                dates = [row['date'] for row in data]
                
                trend_direction = self._calculate_trend(values)
                
                return {
                    "metric": metric,
                    "period": f"{days} days",
                    "data": [
                        {
                            "date": dates[i],
                            "value": round(values[i], 2) if values[i] else 0
                        }
                        for i in range(len(dates))
                    ],
                    "trend": trend_direction,
                    "average": round(statistics.mean(values), 2) if values else 0,
                    "min": round(min(values), 2) if values else 0,
                    "max": round(max(values), 2) if values else 0,
                    "change_percent": self._calculate_change_percent(values) if len(values) > 1 else 0
                }
        except Exception as e:
            return {"error": str(e)}
    
    def get_top_performers(self, limit: int = 10, hours: int = 24) -> Dict:
        """Get best performing endpoints"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = datetime.now() - timedelta(hours=hours)
                
                # Fastest endpoints
                fastest = conn.execute("""
                    SELECT 
                        endpoint,
                        AVG(response_time) as avg_time,
                        COUNT(*) as count
                    FROM request_logs
                    WHERE timestamp > ? AND response_time IS NOT NULL
                    GROUP BY endpoint
                    HAVING count >= 5
                    ORDER BY avg_time ASC
                    LIMIT ?
                """, (cutoff, limit)).fetchall()
                
                # Most reliable (highest success rate)
                reliable = conn.execute("""
                    SELECT 
                        endpoint,
                        COUNT(*) as total,
                        SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) as success,
                        CAST(SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as success_rate
                    FROM request_logs
                    WHERE timestamp > ?
                    GROUP BY endpoint
                    HAVING total >= 5
                    ORDER BY success_rate DESC
                    LIMIT ?
                """, (cutoff, limit)).fetchall()
                
                # Most used
                popular = conn.execute("""
                    SELECT 
                        endpoint,
                        COUNT(*) as count,
                        AVG(response_time) as avg_time
                    FROM request_logs
                    WHERE timestamp > ?
                    GROUP BY endpoint
                    ORDER BY count DESC
                    LIMIT ?
                """, (cutoff, limit)).fetchall()
                
                return {
                    "period": f"{hours}h",
                    "fastest_endpoints": [
                        {
                            "endpoint": row['endpoint'],
                            "avg_response_time": round(row['avg_time'], 3),
                            "request_count": row['count']
                        }
                        for row in fastest
                    ],
                    "most_reliable": [
                        {
                            "endpoint": row['endpoint'],
                            "success_rate": round(row['success_rate'], 2),
                            "total_requests": row['total']
                        }
                        for row in reliable
                    ],
                    "most_popular": [
                        {
                            "endpoint": row['endpoint'],
                            "request_count": row['count'],
                            "avg_response_time": round(row['avg_time'], 3) if row['avg_time'] else 0
                        }
                        for row in popular
                    ]
                }
        except Exception as e:
            return {"error": str(e)}
    
    def get_comparison(self, endpoint1: str, endpoint2: str, hours: int = 24) -> Dict:
        """Compare two endpoints"""
        try:
            stats1 = self.get_endpoint_analytics(endpoint1, hours)
            stats2 = self.get_endpoint_analytics(endpoint2, hours)
            
            if "error" in stats1 or "error" in stats2:
                return {"error": "One or both endpoints have no data"}
            
            return {
                "period": f"{hours}h",
                "endpoint1": {
                    "name": endpoint1,
                    "requests": stats1['total_requests'],
                    "avg_time": stats1['avg_response_time'],
                    "success_rate": stats1['success_rate']
                },
                "endpoint2": {
                    "name": endpoint2,
                    "requests": stats2['total_requests'],
                    "avg_time": stats2['avg_response_time'],
                    "success_rate": stats2['success_rate']
                },
                "comparison": {
                    "faster": endpoint1 if stats1['avg_response_time'] < stats2['avg_response_time'] else endpoint2,
                    "speed_difference": abs(stats1['avg_response_time'] - stats2['avg_response_time']),
                    "more_reliable": endpoint1 if stats1['success_rate'] > stats2['success_rate'] else endpoint2,
                    "reliability_difference": abs(stats1['success_rate'] - stats2['success_rate']),
                    "more_popular": endpoint1 if stats1['total_requests'] > stats2['total_requests'] else endpoint2,
                    "popularity_difference": abs(stats1['total_requests'] - stats2['total_requests'])
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_health_score(self, hours: int = 24) -> Dict:
        """Calculate overall API health score"""
        try:
            summary = self.get_usage_summary(hours)
            
            if "error" in summary:
                return {"error": summary["error"]}
            
            # Calculate score components (0-100 each)
            success_score = summary['success_rate']
            
            # Response time score (inverse - faster is better)
            # Assuming < 100ms is excellent, > 1000ms is poor
            avg_time = summary['avg_response_time']
            if avg_time < 100:
                speed_score = 100
            elif avg_time > 1000:
                speed_score = 0
            else:
                speed_score = 100 - ((avg_time - 100) / 900 * 100)
            
            # Availability score (based on error rate)
            availability_score = 100 - summary['error_rate']
            
            # Overall health score (weighted average)
            health_score = (
                success_score * 0.4 +
                speed_score * 0.3 +
                availability_score * 0.3
            )
            
            # Determine health status
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 75:
                status = "good"
            elif health_score >= 50:
                status = "fair"
            else:
                status = "poor"
            
            return {
                "health_score": round(health_score, 2),
                "status": status,
                "components": {
                    "success_rate": round(success_score, 2),
                    "speed_score": round(speed_score, 2),
                    "availability_score": round(availability_score, 2)
                },
                "metrics": {
                    "total_requests": summary['total_requests'],
                    "avg_response_time": summary['avg_response_time'],
                    "error_rate": summary['error_rate']
                },
                "period": f"{hours}h"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_percentiles(self, values: List[float]) -> Dict:
        """Calculate percentile values"""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        def percentile(p):
            k = (n - 1) * p / 100
            f = int(k)
            c = f + 1 if (f + 1) < n else f
            if f == c:
                return sorted_values[f]
            return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)
        
        return {
            "p50": round(percentile(50), 3),
            "p75": round(percentile(75), 3),
            "p90": round(percentile(90), 3),
            "p95": round(percentile(95), 3),
            "p99": round(percentile(99), 3)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Threshold for determining trend
        threshold = statistics.stdev(values) * 0.1 if len(values) > 1 else 0
        
        if slope > threshold:
            return "increasing"
        elif slope < -threshold:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_change_percent(self, values: List[float]) -> float:
        """Calculate percent change from first to last value"""
        if len(values) < 2 or values[0] == 0:
            return 0.0
        
        return round(((values[-1] - values[0]) / values[0]) * 100, 2)

# Test code
if __name__ == "__main__":
    print("🔬 Testing Analytics Engine...")
    
    engine = AnalyticsEngine()
    
    print("\n📊 Usage Summary (24h):")
    summary = engine.get_usage_summary(24)
    print(json.dumps(summary, indent=2))
    
    print("\n🏥 Health Score:")
    health = engine.get_health_score(24)
    print(json.dumps(health, indent=2))
    
    print("\n🏆 Top Performers:")
    performers = engine.get_top_performers(5, 24)
    print(json.dumps(performers, indent=2))
    
    print("\n📈 Trend Analysis (Requests):")
    trend = engine.get_trend_analysis("requests", 7)
    print(json.dumps(trend, indent=2))
    
    print("\n⚠️ Anomaly Detection:")
    anomalies = engine.detect_anomalies(24, 2.0)
    print(json.dumps(anomalies, indent=2))
    
    print("\n✅ Analytics Engine test complete!")
