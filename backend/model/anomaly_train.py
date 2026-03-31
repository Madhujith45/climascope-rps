"""
ClimaScope - Anomaly Detection Model Training
Implements Isolation Forest for multi-sensor anomaly detection
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

class AnomalyDetector:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.processed_df = None
        self.anomaly_model = None
        self.scaler = None
        self.feature_columns = []
        
    def load_and_preprocess_data(self):
        """Load and preprocess data for anomaly detection"""
        print("=" * 60)
        print("ANOMALY DETECTION - DATA LOADING & PREPROCESSING")
        print("=" * 60)
        
        # Load the same dataset used for regression
        self.df = pd.read_excel(self.data_path)
        print(f"Dataset Shape: {self.df.shape}")
        
        # Make a copy for anomaly detection
        self.processed_df = self.df.copy()
        
        # Handle missing values
        numeric_columns = self.processed_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if self.processed_df[col].isnull().sum() > 0:
                median_val = self.processed_df[col].median()
                self.processed_df[col].fillna(median_val, inplace=True)
        
        # Convert timestamp
        timestamp_cols = [col for col in self.processed_df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if timestamp_cols:
            timestamp_col = timestamp_cols[0]
            self.processed_df[timestamp_col] = pd.to_datetime(self.processed_df[timestamp_col])
            self.processed_df.sort_values(timestamp_col, inplace=True)
        
        # Handle outliers (less aggressive for anomaly detection)
        for col in ['BMP Temp (C)', 'DHT Temp (C)', 'Humidity (%)', 'Pressure (hPa)', 'Gas Voltage (V)', 'Gas PPM']:
            if col in self.processed_df.columns:
                Q1 = self.processed_df[col].quantile(0.05)  # More lenient
                Q3 = self.processed_df[col].quantile(0.95)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR  # More lenient bounds
                upper_bound = Q3 + 3 * IQR
                
                # Don't cap, just identify for analysis
                outliers = self.processed_df[(self.processed_df[col] < lower_bound) | 
                                       (self.processed_df[col] > upper_bound)]
                if len(outliers) > 0:
                    print(f"Found {len(outliers)} potential outliers in {col}")
        
        print("Data preprocessing completed for anomaly detection!")
        return self.processed_df
    
    def create_anomaly_features(self):
        """Create features specifically for anomaly detection"""
        print("\n" + "=" * 60)
        print("CREATING ANOMALY DETECTION FEATURES")
        print("=" * 60)
        
        # Core sensor features
        sensor_features = ['BMP Temp (C)', 'DHT Temp (C)', 'Humidity (%)', 
                        'Pressure (hPa)', 'Gas Voltage (V)', 'Gas PPM']
        
        # Filter to available columns
        available_sensors = [col for col in sensor_features if col in self.processed_df.columns]
        print(f"Available sensors: {available_sensors}")
        
        # Create rolling statistics for anomaly detection
        window_sizes = [3, 5, 10]  # Multiple windows for different anomaly types
        
        for window in window_sizes:
            for sensor in available_sensors:
                # Rolling mean
                self.processed_df[f'{sensor}_rolling_mean_{window}'] = (
                    self.processed_df[sensor].rolling(window=window, min_periods=1).mean()
                )
                
                # Rolling std (important for anomaly detection)
                self.processed_df[f'{sensor}_rolling_std_{window}'] = (
                    self.processed_df[sensor].rolling(window=window, min_periods=1).std().fillna(0.1)
                )
                
                # Rolling range (max - min)
                self.processed_df[f'{sensor}_rolling_range_{window}'] = (
                    self.processed_df[sensor].rolling(window=window, min_periods=1).max() - 
                    self.processed_df[sensor].rolling(window=window, min_periods=1).min()
                ).fillna(0)
        
        # Rate of change (important for sudden spikes)
        for sensor in available_sensors:
            self.processed_df[f'{sensor}_roc_1'] = (
                self.processed_df[sensor].diff(1).fillna(0)
            )
            self.processed_df[f'{sensor}_roc_2'] = (
                self.processed_df[sensor].diff(2).fillna(0)
            )
        
        # Multi-sensor interaction features
        if all(col in self.processed_df.columns for col in ['DHT Temp (C)', 'Humidity (%)']):
            # Heat index approximation
            self.processed_df['heat_index'] = (
                self.processed_df['DHT Temp (C)'] + 
                0.5 * self.processed_df['Humidity (%)'] / 10
            )
        
        if all(col in self.processed_df.columns for col in ['Pressure (hPa)', 'Gas PPM']):
            # Environmental stress indicator
            self.processed_df['env_stress'] = (
                (self.processed_df['Gas PPM'] / 200) *  # Normalize gas
                (1013.25 / self.processed_df['Pressure (hPa)'])  # Inverse pressure
            )
        
        # Time-based features
        timestamp_cols = [col for col in self.processed_df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if timestamp_cols:
            timestamp_col = timestamp_cols[0]
            self.processed_df['hour'] = self.processed_df[timestamp_col].dt.hour
            self.processed_df['is_night'] = ((self.processed_df['hour'] < 6) | 
                                         (self.processed_df['hour'] > 20)).astype(int)
        
        print(f"Created {len(self.processed_df.columns)} total features for anomaly detection")
        return self.processed_df
    
    def train_isolation_forest(self):
        """Train Isolation Forest model for anomaly detection"""
        print("\n" + "=" * 60)
        print("TRAINING ISOLATION FOREST MODEL")
        print("=" * 60)
        
        # Select features for anomaly detection
        feature_cols = []
        
        # Core sensor readings
        sensor_features = ['BMP Temp (C)', 'DHT Temp (C)', 'Humidity (%)', 
                        'Pressure (hPa)', 'Gas Voltage (V)', 'Gas PPM']
        available_sensors = [col for col in sensor_features if col in self.processed_df.columns]
        feature_cols.extend(available_sensors)
        
        # Rolling statistics (use medium window for balance)
        for sensor in available_sensors:
            feature_cols.extend([
                f'{sensor}_rolling_mean_5',
                f'{sensor}_rolling_std_5',
                f'{sensor}_roc_1'
            ])
        
        # Multi-sensor features
        multi_sensor_features = ['heat_index', 'env_stress']
        for feature in multi_sensor_features:
            if feature in self.processed_df.columns:
                feature_cols.append(feature)
        
        # Filter to existing columns
        self.feature_columns = [col for col in feature_cols if col in self.processed_df.columns]
        print(f"Using {len(self.feature_columns)} features for anomaly detection")
        
        # Prepare training data
        X = self.processed_df[self.feature_columns].fillna(0)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        # Why Isolation Forest?
        print("\n🔍 WHY ISOLATION FOREST?")
        print("=" * 40)
        print("1. Unsupervised Learning: No labeled anomaly data needed")
        print("2. Multi-dimensional: Detects anomalies across all sensor dimensions")
        print("3. Robust: Works well with different types of anomalies")
        print("4. Fast: Efficient for real-time applications")
        print("5. Interpretable: Provides anomaly scores")
        print("\n🧠 HOW IT WORKS?")
        print("=" * 40)
        print("1. Random Forest builds isolation trees")
        print("2. Anomalies are easier to isolate (shorter paths)")
        print("3. Average path length determines anomaly score")
        print("4. Lower path length = higher anomaly probability")
        
        # Configure model for IoT sensor data
        self.anomaly_model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=0.05,  # Expect 5% anomalies
            max_features=1.0,
            bootstrap=False,
            random_state=42,
            n_jobs=-1
        )
        
        # Train model
        print("\n🚀 Training Isolation Forest...")
        self.anomaly_model.fit(X_scaled)
        
        # Get predictions and scores
        predictions = self.anomaly_model.predict(X_scaled)
        scores = self.anomaly_model.decision_function(X_scaled)
        
        # Add to dataframe for analysis
        self.processed_df['anomaly_prediction'] = predictions
        self.processed_df['anomaly_score'] = scores
        
        # Analyze results
        anomaly_count = sum(predictions == -1)
        normal_count = sum(predictions == 1)
        
        print(f"\n📊 TRAINING RESULTS:")
        print(f"Total samples: {len(predictions)}")
        print(f"Normal samples: {normal_count} ({normal_count/len(predictions)*100:.1f}%)")
        print(f"Anomaly samples: {anomaly_count} ({anomaly_count/len(predictions)*100:.1f}%)")
        print(f"Expected contamination: 5.0%")
        print(f"Actual contamination: {anomaly_count/len(predictions)*100:.1f}%")
        
        # Score distribution
        print(f"\n📈 ANOMALY SCORE DISTRIBUTION:")
        print(f"Min score: {scores.min():.4f}")
        print(f"Max score: {scores.max():.4f}")
        print(f"Mean score: {scores.mean():.4f}")
        print(f"Std deviation: {scores.std():.4f}")
        
        # Find threshold (typically around 0)
        threshold = 0
        print(f"Anomaly threshold: {threshold:.4f}")
        
        return {
            'anomaly_count': anomaly_count,
            'normal_count': normal_count,
            'contamination_rate': anomaly_count/len(predictions),
            'threshold': threshold
        }
    
    def analyze_anomaly_patterns(self):
        """Analyze patterns in detected anomalies"""
        print("\n" + "=" * 60)
        print("ANOMALY PATTERN ANALYSIS")
        print("=" * 60)
        
        anomalies = self.processed_df[self.processed_df['anomaly_prediction'] == -1]
        
        if len(anomalies) == 0:
            print("No anomalies detected in training data")
            return
        
        print(f"Analyzing {len(anomalies)} detected anomalies...")
        
        # Temperature patterns
        if 'DHT Temp (C)' in anomalies.columns:
            temp_anomalies = anomalies['DHT Temp (C)']
            print(f"\n🌡️  TEMPERATURE ANOMALIES:")
            print(f"  Avg temp during anomalies: {temp_anomalies.mean():.2f}°C")
            print(f"  Temp range: {temp_anomalies.min():.2f}°C - {temp_anomalies.max():.2f}°C")
            print(f"  Global avg temp: {self.processed_df['DHT Temp (C)'].mean():.2f}°C")
        
        # Gas patterns
        if 'Gas PPM' in anomalies.columns:
            gas_anomalies = anomalies['Gas PPM']
            print(f"\n💨 GAS ANOMALIES:")
            print(f"  Avg gas during anomalies: {gas_anomalies.mean():.1f} PPM")
            print(f"  Gas range: {gas_anomalies.min():.1f} - {gas_anomalies.max():.1f} PPM")
            print(f"  Global avg gas: {self.processed_df['Gas PPM'].mean():.1f} PPM")
        
        # Pressure patterns
        if 'Pressure (hPa)' in anomalies.columns:
            pressure_anomalies = anomalies['Pressure (hPa)']
            print(f"\n🔵 PRESSURE ANOMALIES:")
            print(f"  Avg pressure during anomalies: {pressure_anomalies.mean():.1f} hPa")
            print(f"  Pressure range: {pressure_anomalies.min():.1f} - {pressure_anomalies.max():.1f} hPa")
            print(f"  Global avg pressure: {self.processed_df['Pressure (hPa)'].mean():.1f} hPa")
        
        # Time patterns
        timestamp_cols = [col for col in anomalies.columns if 'time' in col.lower() or 'date' in col.lower()]
        if timestamp_cols:
            timestamp_col = timestamp_cols[0]
            anomalies['hour'] = pd.to_datetime(anomalies[timestamp_col]).dt.hour
            
            hour_counts = anomalies['hour'].value_counts().sort_index()
            print(f"\n⏰ TIME PATTERNS:")
            for hour, count in hour_counts.items():
                print(f"  {hour:02d}:00 - {count} anomalies")
    
    def save_anomaly_model(self):
        """Save the trained anomaly detection model"""
        print("\n" + "=" * 60)
        print("SAVING ANOMALY DETECTION MODEL")
        print("=" * 60)
        
        # Create directory
        os.makedirs('saved_models', exist_ok=True)
        
        # Save model components
        model_path = 'saved_models/anomaly_model.pkl'
        scaler_path = 'saved_models/anomaly_preprocessor.pkl'
        features_path = 'saved_models/anomaly_features.pkl'
        
        joblib.dump(self.anomaly_model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_columns, features_path)
        
        print(f"✅ Anomaly model saved to: {model_path}")
        print(f"✅ Preprocessor saved to: {scaler_path}")
        print(f"✅ Feature columns saved to: {features_path}")
        
        return {
            'model_path': model_path,
            'scaler_path': scaler_path,
            'features_path': features_path
        }
    
    def visualize_anomalies(self):
        """Create visualizations of anomaly detection results"""
        print("\n" + "=" * 60)
        print("CREATING ANOMALY VISUALIZATIONS")
        print("=" * 60)
        
        # Create plots directory
        os.makedirs('anomaly_plots', exist_ok=True)
        
        # Plot 1: Temperature with anomalies
        if 'DHT Temp (C)' in self.processed_df.columns:
            plt.figure(figsize=(15, 8))
            
            # Sample data for visualization
            sample_size = min(1000, len(self.processed_df))
            step = len(self.processed_df) // sample_size
            sampled_df = self.processed_df.iloc[::step].copy()
            
            # Sort by timestamp if available
            timestamp_cols = [col for col in sampled_df.columns if 'time' in col.lower() or 'date' in col.lower()]
            if timestamp_cols:
                timestamp_col = timestamp_cols[0]
                sampled_df = sampled_df.sort_values(timestamp_col)
                x_axis = range(len(sampled_df))
            else:
                x_axis = range(len(sampled_df))
            
            # Plot temperature
            plt.subplot(2, 2, 1)
            normal_mask = sampled_df['anomaly_prediction'] == 1
            anomaly_mask = sampled_df['anomaly_prediction'] == -1
            
            normal_indices = sampled_df[normal_mask].index.tolist()
            anomaly_indices = sampled_df[anomaly_mask].index.tolist()
            
            plt.plot(normal_indices, sampled_df.loc[normal_mask, 'DHT Temp (C)'], 
                    'b.', label='Normal', alpha=0.6)
            plt.plot(anomaly_indices, sampled_df.loc[anomaly_mask, 'DHT Temp (C)'], 
                    'r.', label='Anomaly', markersize=8)
            plt.title('Temperature Anomalies')
            plt.xlabel('Time Index')
            plt.ylabel('Temperature (°C)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Plot gas
            plt.subplot(2, 2, 2)
            plt.plot(normal_indices, sampled_df.loc[normal_mask, 'Gas PPM'], 
                    'g.', label='Normal', alpha=0.6)
            plt.plot(anomaly_indices, sampled_df.loc[anomaly_mask, 'Gas PPM'], 
                    'r.', label='Anomaly', markersize=8)
            plt.title('Gas Anomalies')
            plt.xlabel('Time Index')
            plt.ylabel('Gas (PPM)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Plot anomaly scores
            plt.subplot(2, 2, 3)
            plt.plot(x_axis, sampled_df['anomaly_score'], 'b-', alpha=0.7)
            plt.axhline(y=0, color='r', linestyle='--', label='Anomaly Threshold')
            plt.title('Anomaly Scores')
            plt.xlabel('Time Index')
            plt.ylabel('Anomaly Score')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Score distribution
            plt.subplot(2, 2, 4)
            plt.hist(sampled_df['anomaly_score'], bins=30, alpha=0.7, color='skyblue')
            plt.axvline(x=0, color='r', linestyle='--', label='Threshold')
            plt.title('Anomaly Score Distribution')
            plt.xlabel('Anomaly Score')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('anomaly_plots/anomaly_detection_overview.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print("✅ Anomaly visualization saved to: anomaly_plots/anomaly_detection_overview.png")
        
        return True

def main():
    """Main function to train anomaly detection model"""
    print("🚨 ClimaScope - Anomaly Detection Model Training")
    print("Advanced AI Intelligence System")
    
    # Initialize anomaly detector
    data_path = r"D:\climascope\sensor_data.xlsx"
    detector = AnomalyDetector(data_path)
    
    try:
        # Step 1: Load and preprocess data
        detector.load_and_preprocess_data()
        
        # Step 2: Create anomaly-specific features
        detector.create_anomaly_features()
        
        # Step 3: Train Isolation Forest
        results = detector.train_isolation_forest()
        
        # Step 4: Analyze anomaly patterns
        detector.analyze_anomaly_patterns()
        
        # Step 5: Visualize results
        detector.visualize_anomalies()
        
        # Step 6: Save model
        saved_paths = detector.save_anomaly_model()
        
        print("\n" + "=" * 60)
        print("🎉 ANOMALY DETECTION TRAINING COMPLETED!")
        print("=" * 60)
        print("Summary:")
        print(f"- Anomaly detection model trained successfully")
        print(f"- Contamination rate: {results['contamination_rate']*100:.1f}%")
        print(f"- Features used: {len(detector.feature_columns)}")
        print(f"- Model saved to: {saved_paths['model_path']}")
        print("\nReady for integration with prediction system!")
        
    except Exception as e:
        print(f"❌ Error in anomaly detection training: {str(e)}")
        raise

if __name__ == "__main__":
    main()
