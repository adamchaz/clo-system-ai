#!/usr/bin/env python3
"""
Compare MAG17 vs MAG11 CLO Deals
Comprehensive analysis of portfolio composition, performance, and characteristics
"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import json

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'database': 'clo_dev',
    'user': 'postgres',
    'password': 'adamchaz'
}

def get_deal_overview(cursor, deal_id):
    """Get basic deal information"""
    cursor.execute("""
        SELECT 
            deal_id,
            deal_name,
            manager_name,
            pricing_date,
            effective_date,
            maturity_date,
            target_par_amount,
            deal_status
        FROM clo_deals 
        WHERE deal_id = %s
    """, (deal_id,))
    
    return cursor.fetchone()

def get_asset_metrics(cursor, deal_id):
    """Get comprehensive asset metrics for a deal"""
    cursor.execute("""
        SELECT 
            COUNT(*) as asset_count,
            SUM(COALESCE(a.par_amount, 0)) as total_par,
            AVG(COALESCE(a.par_amount, 0)) as avg_par,
            MIN(COALESCE(a.par_amount, 0)) as min_par,
            MAX(COALESCE(a.par_amount, 0)) as max_par,
            COUNT(CASE WHEN a.par_amount > 0 THEN 1 END) as assets_with_par,
            SUM(CASE WHEN a.par_amount > 0 THEN a.par_amount ELSE 0 END) as active_par
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = %s
    """, (deal_id,))
    
    return cursor.fetchone()

def get_rating_distribution(cursor, deal_id):
    """Get credit rating distribution"""
    cursor.execute("""
        SELECT 
            COALESCE(a.mdy_rating, 'Not Rated') as rating,
            COUNT(*) as count,
            SUM(COALESCE(a.par_amount, 0)) as par_amount,
            ROUND(AVG(COALESCE(a.par_amount, 0)), 2) as avg_par
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = %s
        GROUP BY COALESCE(a.mdy_rating, 'Not Rated')
        ORDER BY par_amount DESC
    """, (deal_id,))
    
    return cursor.fetchall()

def get_industry_distribution(cursor, deal_id):
    """Get industry distribution"""
    cursor.execute("""
        SELECT 
            COALESCE(a.mdy_industry, 'Unknown') as industry,
            COUNT(*) as count,
            SUM(COALESCE(a.par_amount, 0)) as par_amount,
            ROUND(AVG(COALESCE(a.par_amount, 0)), 2) as avg_par
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = %s AND a.par_amount > 0
        GROUP BY COALESCE(a.mdy_industry, 'Unknown')
        ORDER BY par_amount DESC
        LIMIT 10
    """, (deal_id,))
    
    return cursor.fetchall()

def get_country_distribution(cursor, deal_id):
    """Get country distribution"""
    cursor.execute("""
        SELECT 
            COALESCE(a.country, 'Unknown') as country,
            COUNT(*) as count,
            SUM(COALESCE(a.par_amount, 0)) as par_amount
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = %s AND a.par_amount > 0
        GROUP BY COALESCE(a.country, 'Unknown')
        ORDER BY par_amount DESC
    """, (deal_id,))
    
    return cursor.fetchall()

def get_seniority_distribution(cursor, deal_id):
    """Get seniority distribution"""
    cursor.execute("""
        SELECT 
            COALESCE(a.seniority, 'Unknown') as seniority,
            COUNT(*) as count,
            SUM(COALESCE(a.par_amount, 0)) as par_amount
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = %s AND a.par_amount > 0
        GROUP BY COALESCE(a.seniority, 'Unknown')
        ORDER BY par_amount DESC
    """, (deal_id,))
    
    return cursor.fetchall()

def get_top_assets(cursor, deal_id, limit=10):
    """Get top assets by par amount"""
    cursor.execute("""
        SELECT 
            a.blkrock_id,
            a.issue_name,
            a.issuer_name,
            a.par_amount,
            a.mdy_rating,
            a.sp_rating,
            a.mdy_industry,
            a.country,
            a.seniority
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = %s AND a.par_amount > 0
        ORDER BY a.par_amount DESC
        LIMIT %s
    """, (deal_id, limit))
    
    return cursor.fetchall()

def format_currency(amount):
    """Format currency with appropriate scale"""
    if amount >= 1_000_000:
        return f"${amount/1_000_000:,.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:,.1f}K"
    else:
        return f"${amount:,.2f}"

def print_deal_comparison(deal1_data, deal2_data):
    """Print comprehensive deal comparison"""
    
    print("=" * 100)
    print("                         MAG17 vs MAG11 CLO DEAL COMPARISON")
    print("=" * 100)
    
    # Basic deal information
    print("\nDEAL OVERVIEW")
    print("-" * 80)
    print(f"{'Metric':<25} {'MAG17':<35} {'MAG11':<35}")
    print("-" * 80)
    
    mag17_deal = deal1_data['deal_info']
    mag11_deal = deal2_data['deal_info']
    
    print(f"{'Deal Name':<25} {mag17_deal['deal_name']:<35} {mag11_deal['deal_name']:<35}")
    print(f"{'Manager':<25} {mag17_deal['manager_name']:<35} {mag11_deal['manager_name']:<35}")
    print(f"{'Pricing Date':<25} {mag17_deal['pricing_date']:<35} {mag11_deal['pricing_date']:<35}")
    print(f"{'Effective Date':<25} {mag17_deal['effective_date']:<35} {mag11_deal['effective_date']:<35}")
    print(f"{'Maturity Date':<25} {mag17_deal['maturity_date']:<35} {mag11_deal['maturity_date']:<35}")
    print(f"{'Target Par':<25} {format_currency(float(mag17_deal['target_par_amount'])):<35} {format_currency(float(mag11_deal['target_par_amount'])):<35}")
    print(f"{'Deal Status':<25} {mag17_deal['deal_status']:<35} {mag11_deal['deal_status']:<35}")
    
    # Portfolio metrics
    print(f"\nPORTFOLIO METRICS")
    print("-" * 80)
    print(f"{'Metric':<25} {'MAG17':<35} {'MAG11':<35}")
    print("-" * 80)
    
    mag17_assets = deal1_data['asset_metrics']
    mag11_assets = deal2_data['asset_metrics']
    
    print(f"{'Asset Count':<25} {mag17_assets['asset_count']:<35} {mag11_assets['asset_count']:<35}")
    print(f"{'Total Par':<25} {format_currency(float(mag17_assets['total_par'])):<35} {format_currency(float(mag11_assets['total_par'])):<35}")
    print(f"{'Average Par':<25} {format_currency(float(mag17_assets['avg_par'])):<35} {format_currency(float(mag11_assets['avg_par'])):<35}")
    print(f"{'Min Par':<25} {format_currency(float(mag17_assets['min_par'])):<35} {format_currency(float(mag11_assets['min_par'])):<35}")
    print(f"{'Max Par':<25} {format_currency(float(mag17_assets['max_par'])):<35} {format_currency(float(mag11_assets['max_par'])):<35}")
    
    # Coverage ratios
    mag17_coverage = float(mag17_assets['total_par']) / float(mag17_deal['target_par_amount']) * 100
    mag11_coverage = float(mag11_assets['total_par']) / float(mag11_deal['target_par_amount']) * 100
    
    print(f"{'Portfolio Coverage':<25} {mag17_coverage:.1f}%{'':<29} {mag11_coverage:.1f}%{'':<29}")
    
    # Top credit ratings
    print(f"\nTOP CREDIT RATINGS")
    print("-" * 80)
    print("MAG17 Rating Distribution:")
    for rating in deal1_data['ratings'][:5]:
        pct = float(rating['par_amount']) / float(mag17_assets['total_par']) * 100 if float(mag17_assets['total_par']) > 0 else 0
        print(f"  {rating['rating']:<8}: {rating['count']:>3} assets, {format_currency(float(rating['par_amount'])):>8} ({pct:>4.1f}%)")
    
    print("\nMAG11 Rating Distribution:")
    for rating in deal2_data['ratings'][:5]:
        pct = float(rating['par_amount']) / float(mag11_assets['total_par']) * 100 if float(mag11_assets['total_par']) > 0 else 0
        print(f"  {rating['rating']:<8}: {rating['count']:>3} assets, {format_currency(float(rating['par_amount'])):>8} ({pct:>4.1f}%)")
    
    # Top industries
    print(f"\nTOP INDUSTRIES")
    print("-" * 80)
    print("MAG17 Top Industries:")
    for industry in deal1_data['industries'][:5]:
        pct = float(industry['par_amount']) / float(mag17_assets['active_par']) * 100 if float(mag17_assets['active_par']) > 0 else 0
        print(f"  {industry['industry'][:30]:<30}: {industry['count']:>3} assets, {format_currency(float(industry['par_amount'])):>8} ({pct:>4.1f}%)")
    
    print("\nMAG11 Top Industries:")
    for industry in deal2_data['industries'][:5]:
        pct = float(industry['par_amount']) / float(mag11_assets['active_par']) * 100 if float(mag11_assets['active_par']) > 0 else 0
        print(f"  {industry['industry'][:30]:<30}: {industry['count']:>3} assets, {format_currency(float(industry['par_amount'])):>8} ({pct:>4.1f}%)")
    
    # Geographic distribution
    print(f"\nGEOGRAPHIC DISTRIBUTION")
    print("-" * 80)
    print("MAG17 Countries:")
    for country in deal1_data['countries'][:5]:
        pct = float(country['par_amount']) / float(mag17_assets['active_par']) * 100 if float(mag17_assets['active_par']) > 0 else 0
        print(f"  {country['country']:<20}: {country['count']:>3} assets, {format_currency(float(country['par_amount'])):>8} ({pct:>4.1f}%)")
    
    print("\nMAG11 Countries:")
    for country in deal2_data['countries'][:5]:
        pct = float(country['par_amount']) / float(mag11_assets['active_par']) * 100 if float(mag11_assets['active_par']) > 0 else 0
        print(f"  {country['country']:<20}: {country['count']:>3} assets, {format_currency(float(country['par_amount'])):>8} ({pct:>4.1f}%)")
    
    # Seniority distribution
    print(f"\nSENIORITY DISTRIBUTION")
    print("-" * 80)
    print("MAG17 Seniority:")
    for seniority in deal1_data['seniority']:
        pct = float(seniority['par_amount']) / float(mag17_assets['active_par']) * 100 if float(mag17_assets['active_par']) > 0 else 0
        print(f"  {seniority['seniority']:<20}: {seniority['count']:>3} assets, {format_currency(float(seniority['par_amount'])):>8} ({pct:>4.1f}%)")
    
    print("\nMAG11 Seniority:")
    for seniority in deal2_data['seniority']:
        pct = float(seniority['par_amount']) / float(mag11_assets['active_par']) * 100 if float(mag11_assets['active_par']) > 0 else 0
        print(f"  {seniority['seniority']:<20}: {seniority['count']:>3} assets, {format_currency(float(seniority['par_amount'])):>8} ({pct:>4.1f}%)")
    
    # Top holdings
    print(f"\nTOP 5 LARGEST HOLDINGS")
    print("-" * 80)
    print("MAG17 Top Holdings:")
    for i, asset in enumerate(deal1_data['top_assets'][:5], 1):
        print(f"  {i}. {asset['issue_name'][:40]:<40} {format_currency(float(asset['par_amount'])):>10} ({asset['mdy_rating'] or 'NR'})")
    
    print("\nMAG11 Top Holdings:")
    for i, asset in enumerate(deal2_data['top_assets'][:5], 1):
        print(f"  {i}. {asset['issue_name'][:40]:<40} {format_currency(float(asset['par_amount'])):>10} ({asset['mdy_rating'] or 'NR'})")
    
    # Summary comparison
    print(f"\nKEY DIFFERENCES SUMMARY")
    print("-" * 80)
    
    # Vintage comparison
    years_diff = mag17_deal['effective_date'].year - mag11_deal['effective_date'].year
    print(f"- Vintage Difference: MAG17 is {years_diff} year(s) newer than MAG11")
    
    # Size comparison
    size_diff = float(mag17_deal['target_par_amount']) - float(mag11_deal['target_par_amount'])
    print(f"- Size Difference: MAG17 target is {format_currency(abs(size_diff))} {'larger' if size_diff > 0 else 'smaller'} than MAG11")
    
    # Asset count difference
    count_diff = mag17_assets['asset_count'] - mag11_assets['asset_count']
    print(f"- Portfolio Size: MAG17 has {abs(count_diff)} {'more' if count_diff > 0 else 'fewer'} assets than MAG11")
    
    # Coverage difference
    coverage_diff = mag17_coverage - mag11_coverage
    print(f"- Data Coverage: MAG17 has {coverage_diff:+.1f}% coverage vs MAG11")
    
    # Concentration difference
    mag17_avg = float(mag17_assets['avg_par'])
    mag11_avg = float(mag11_assets['avg_par'])
    print(f"- Average Position: MAG17 avg {format_currency(mag17_avg)} vs MAG11 avg {format_currency(mag11_avg)}")
    
    print("=" * 100)

def main():
    """Main comparison function"""
    print("Starting MAG17 vs MAG11 Comparison Analysis...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Gather data for both deals
        deals_data = {}
        
        for deal_id in ['MAG17', 'MAG11']:
            print(f"Analyzing {deal_id}...")
            
            deals_data[deal_id] = {
                'deal_info': get_deal_overview(cursor, deal_id),
                'asset_metrics': get_asset_metrics(cursor, deal_id),
                'ratings': get_rating_distribution(cursor, deal_id),
                'industries': get_industry_distribution(cursor, deal_id),
                'countries': get_country_distribution(cursor, deal_id),
                'seniority': get_seniority_distribution(cursor, deal_id),
                'top_assets': get_top_assets(cursor, deal_id, 5)
            }
        
        # Print comprehensive comparison
        print_deal_comparison(deals_data['MAG17'], deals_data['MAG11'])
        
    except Exception as e:
        print(f"Error: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()