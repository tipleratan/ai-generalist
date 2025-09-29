import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from collections import defaultdict
import argparse
import os

class YouTubeAdAnalyzer:
    def __init__(self, json_file_path):
        self.data_file = json_file_path
        self.ad_events = self.load_data()
        self.df = self.create_dataframe()
    
    def load_data(self):
        """Load ad events from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} ad events")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def create_dataframe(self):
        """Convert ad events to pandas DataFrame"""
        if not self.ad_events:
            return pd.DataFrame()
        
        df_data = []
        for event in self.ad_events:
            df_data.append({
                'video_id': event.get('videoId', 'unknown'),
                'ad_type': event.get('adType', 'unknown'),
                'position': event.get('position', 'unknown'),
                'duration': event.get('duration', 0),
                'video_time': event.get('videoTime', 0),
                'timestamp': pd.to_datetime(event.get('startTime', 0), unit='ms')
            })
        
        return pd.DataFrame(df_data)
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        if self.df.empty:
            return "No data available for analysis"
        
        report = []
        report.append("="*60)
        report.append("YOUTUBE AD ANALYTICS REPORT")
        report.append("="*60)
        
        # Basic statistics
        total_ads = len(self.df)
        unique_videos = self.df['video_id'].nunique()
        avg_duration = self.df['duration'].mean()
        
        report.append(f"Total Ads Detected: {total_ads}")
        report.append(f"Unique Videos: {unique_videos}")
        report.append(f"Average Ad Duration: {avg_duration:.1f}s")
        
        # Ad type breakdown
        report.append("\\nAd Type Distribution:")
        ad_types = self.df['ad_type'].value_counts()
        for ad_type, count in ad_types.items():
            percentage = (count / total_ads) * 100
            report.append(f"  {ad_type}: {count} ({percentage:.1f}%)")
        
        # Position analysis
        report.append("\\nAd Position Distribution:")
        positions = self.df['position'].value_counts()
        for position, count in positions.items():
            percentage = (count / total_ads) * 100
            report.append(f"  {position}: {count} ({percentage:.1f}%)")
        
        # Duration analysis
        report.append("\\nDuration Analysis:")
        report.append(f"  Shortest Ad: {self.df['duration'].min():.1f}s")
        report.append(f"  Longest Ad: {self.df['duration'].max():.1f}s")
        report.append(f"  Median Duration: {self.df['duration'].median():.1f}s")
        
        # Video-specific analysis
        if unique_videos > 1:
            report.append("\\nPer-Video Analysis:")
            video_stats = self.df.groupby('video_id').agg({
                'duration': ['count', 'mean', 'sum']
            }).round(1)
            
            for video_id in video_stats.index[:5]:  # Top 5 videos
                ads_count = video_stats.loc[video_id, ('duration', 'count')]
                avg_dur = video_stats.loc[video_id, ('duration', 'mean')]
                total_dur = video_stats.loc[video_id, ('duration', 'sum')]
                report.append(f"  {video_id}: {ads_count} ads, {avg_dur:.1f}s avg, {total_dur:.1f}s total")
        
        # Time-based patterns
        if 'timestamp' in self.df.columns:
            report.append("\\nTemporal Patterns:")
            hourly_dist = self.df['timestamp'].dt.hour.value_counts().sort_index()
            peak_hour = hourly_dist.idxmax()
            report.append(f"  Peak Ad Hour: {peak_hour}:00 ({hourly_dist[peak_hour]} ads)")
            
            daily_dist = self.df['timestamp'].dt.day_name().value_counts()
            peak_day = daily_dist.idxmax()
            report.append(f"  Peak Ad Day: {peak_day} ({daily_dist[peak_day]} ads)")
        
        return "\\n".join(report)
    
    def create_visualizations(self, output_dir="ad_analytics_plots"):
        """Generate visualization plots"""
        if self.df.empty:
            print("No data available for visualization")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 1. Ad Type Distribution
        plt.figure(figsize=(10, 6))
        ad_type_counts = self.df['ad_type'].value_counts()
        plt.pie(ad_type_counts.values, labels=ad_type_counts.index, autopct='%1.1f%%')
        plt.title('Ad Type Distribution')
        plt.savefig(f'{output_dir}/ad_type_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Ad Position Analysis
        plt.figure(figsize=(10, 6))
        position_counts = self.df['position'].value_counts()
        sns.barplot(x=position_counts.index, y=position_counts.values)
        plt.title('Ad Position Distribution')
        plt.ylabel('Count')
        plt.xlabel('Position')
        plt.savefig(f'{output_dir}/ad_position_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Duration Distribution
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        self.df['duration'].hist(bins=20, alpha=0.7, edgecolor='black')
        plt.title('Ad Duration Distribution')
        plt.xlabel('Duration (seconds)')
        plt.ylabel('Frequency')
        
        plt.subplot(1, 2, 2)
        sns.boxplot(y=self.df['duration'])
        plt.title('Ad Duration Box Plot')
        plt.ylabel('Duration (seconds)')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/duration_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Time-based analysis (if timestamp available)
        if 'timestamp' in self.df.columns and len(self.df) > 10:
            plt.figure(figsize=(15, 8))
            
            # Hourly distribution
            plt.subplot(2, 2, 1)
            hourly_dist = self.df['timestamp'].dt.hour.value_counts().sort_index()
            plt.bar(hourly_dist.index, hourly_dist.values)
            plt.title('Ads by Hour of Day')
            plt.xlabel('Hour')
            plt.ylabel('Ad Count')
            
            # Daily distribution
            plt.subplot(2, 2, 2)
            daily_dist = self.df['timestamp'].dt.day_name().value_counts()
            plt.bar(daily_dist.index, daily_dist.values)
            plt.title('Ads by Day of Week')
            plt.xlabel('Day')
            plt.ylabel('Ad Count')
            plt.xticks(rotation=45)
            
            # Timeline
            plt.subplot(2, 1, 2)
            daily_timeline = self.df.set_index('timestamp').resample('D').size()
            daily_timeline.plot(kind='line', marker='o')
            plt.title('Ad Detection Timeline')
            plt.xlabel('Date')
            plt.ylabel('Ads per Day')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/temporal_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"Visualizations saved to {output_dir}/")
    
    def export_processed_data(self, output_file="processed_ad_data.csv"):
        """Export processed data to CSV"""
        if not self.df.empty:
            self.df.to_csv(output_file, index=False)
            print(f"Processed data exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze YouTube ad data from Chrome extension')
    parser.add_argument('json_file', help='Path to JSON file exported from extension')
    parser.add_argument('--output-dir', default='ad_analytics', help='Output directory for reports and plots')
    parser.add_argument('--no-plots', action='store_true', help='Skip generating plots')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"Error: File {args.json_file} not found")
        return
    
    # Initialize analyzer
    analyzer = YouTubeAdAnalyzer(args.json_file)
    
    # Generate summary report
    report = analyzer.generate_summary_report()
    print(report)
    
    # Save report to file
    os.makedirs(args.output_dir, exist_ok=True)
    with open(f'{args.output_dir}/summary_report.txt', 'w') as f:
        f.write(report)
    
    # Generate visualizations
    if not args.no_plots:
        analyzer.create_visualizations(f'{args.output_dir}/plots')
    
    # Export processed data
    analyzer.export_processed_data(f'{args.output_dir}/processed_data.csv')
    
    print(f"\\nAnalysis complete. Results saved to {args.output_dir}/")

if __name__ == "__main__":
    main()
