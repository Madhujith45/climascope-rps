"""
ClimaScope ML Pipeline - Step 1: Data Preprocessing & Analysis
This script handles the complete ML pipeline from data loading to model training
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# Set style for plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class ClimaScopeML:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.processed_df = None
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.target_column = None
        
    def load_and_inspect_data(self):
        """Step 1: Load and inspect the sensor data"""
        print("=" * 50)
        print("STEP 1: DATA LOADING AND INSPECTION")
        print("=" * 50)
        
        # Load the Excel file
        self.df = pd.read_excel(self.data_path)
        
        print(f"Dataset Shape: {self.df.shape}")
        print(f"Columns: {list(self.df.columns)}")
        print("\nFirst 5 rows:")
        print(self.df.head())
        
        print("\nData Types:")
        print(self.df.dtypes)
        
        print("\nMissing Values:")
        print(self.df.isnull().sum())
        
        print("\nBasic Statistics:")
        print(self.df.describe())
        
        return self.df
    
    def preprocess_data(self):
        """Step 2: Data preprocessing"""
        print("\n" + "=" * 50)
        print("STEP 2: DATA PREPROCESSING")
        print("=" * 50)
        
        # Make a copy to avoid modifying original data
        self.processed_df = self.df.copy()
        
        # Handle missing values
        print("Handling missing values...")
        numeric_columns = self.processed_df.select_dtypes(include=[np.number]).columns
        
        # Fill missing numeric values with median (robust to outliers)
        for col in numeric_columns:
            if self.processed_df[col].isnull().sum() > 0:
                median_val = self.processed_df[col].median()
                self.processed_df[col].fillna(median_val, inplace=True)
                print(f"Filled {col} missing values with median: {median_val}")
        
        # Remove duplicates
        initial_rows = len(self.processed_df)
        self.processed_df.drop_duplicates(inplace=True)
        removed_duplicates = initial_rows - len(self.processed_df)
        print(f"Removed {removed_duplicates} duplicate rows")
        
        # Convert timestamp if exists
        timestamp_cols = [col for col in self.processed_df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if timestamp_cols:
            timestamp_col = timestamp_cols[0]
            print(f"Converting {timestamp_col} to datetime...")
            self.processed_df[timestamp_col] = pd.to_datetime(self.processed_df[timestamp_col])
            
            # Sort by timestamp
            self.processed_df.sort_values(timestamp_col, inplace=True)
            print("Data sorted chronologically")
        
        # Detect and handle outliers using IQR method
        print("Detecting and handling outliers...")
        for col in numeric_columns:
            Q1 = self.processed_df[col].quantile(0.25)
            Q3 = self.processed_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = self.processed_df[(self.processed_df[col] < lower_bound) | 
                                       (self.processed_df[col] > upper_bound)]
            
            if len(outliers) > 0:
                print(f"Found {len(outliers)} outliers in {col}")
                # Cap outliers to bounds
                self.processed_df[col] = np.clip(self.processed_df[col], lower_bound, upper_bound)
        
        print("Preprocessing completed!")
        return self.processed_df
    
    def feature_engineering(self):
        """Step 3: Feature Engineering"""
        print("\n" + "=" * 50)
        print("STEP 3: FEATURE ENGINEERING")
        print("=" * 50)
        
        # Get timestamp column if exists
        timestamp_cols = [col for col in self.processed_df.columns if 'time' in col.lower() or 'date' in col.lower()]
        
        if timestamp_cols:
            timestamp_col = timestamp_cols[0]
            
            # Time-based features
            self.processed_df['hour'] = self.processed_df[timestamp_col].dt.hour
            self.processed_df['day_of_week'] = self.processed_df[timestamp_col].dt.dayofweek
            self.processed_df['month'] = self.processed_df[timestamp_col].dt.month
            self.processed_df['is_weekend'] = (self.processed_df['day_of_week'] >= 5).astype(int)
            
            print("Created time-based features: hour, day_of_week, month, is_weekend")
        
        # Get numeric columns for rolling features
        numeric_cols = self.processed_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col not in ['hour', 'day_of_week', 'month', 'is_weekend']]
        
        # Rolling statistics (window=5)
        for col in numeric_cols:
            self.processed_df[f'{col}_rolling_mean_5'] = self.processed_df[col].rolling(window=5, min_periods=1).mean()
            self.processed_df[f'{col}_rolling_std_5'] = self.processed_df[col].rolling(window=5, min_periods=1).std()
            
        print("Created rolling statistics (window=5)")
        
        # Lag features (t-1, t-2)
        for col in numeric_cols:
            self.processed_df[f'{col}_lag_1'] = self.processed_df[col].shift(1)
            self.processed_df[f'{col}_lag_2'] = self.processed_df[col].shift(2)
            
        print("Created lag features (t-1, t-2)")
        
        # Derived features
        if 'temperature' in self.processed_df.columns and 'humidity' in self.processed_df.columns:
            self.processed_df['temp_humidity_ratio'] = self.processed_df['temperature'] / (self.processed_df['humidity'] + 1)
            print("Created temp_humidity_ratio feature")
        
        if 'temperature' in self.processed_df.columns and 'pressure' in self.processed_df.columns:
            self.processed_df['temp_pressure_ratio'] = self.processed_df['temperature'] / (self.processed_df['pressure'] + 1)
            print("Created temp_pressure_ratio feature")
        
        # Handle any remaining NaN values from lag features
        self.processed_df.fillna(method='bfill', inplace=True)
        self.processed_df.fillna(0, inplace=True)
        
        print("Feature engineering completed!")
        return self.processed_df
    
    def exploratory_data_analysis(self):
        """Step 4: Exploratory Data Analysis"""
        print("\n" + "=" * 50)
        print("STEP 4: EXPLORATORY DATA ANALYSIS")
        print("=" * 50)
        
        # Create output directory for plots
        os.makedirs('plots', exist_ok=True)
        
        # Summary statistics
        print("Summary Statistics:")
        print(self.processed_df.describe())
        
        # Correlation matrix
        numeric_cols = self.processed_df.select_dtypes(include=[np.number]).columns
        correlation_matrix = self.processed_df[numeric_cols].corr()
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Correlation Matrix')
        plt.tight_layout()
        plt.savefig('plots/correlation_matrix.png')
        plt.close()
        
        # Feature distributions
        numeric_cols = numeric_cols[:6]  # Limit to first 6 numeric columns for readability
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.ravel()
        
        for i, col in enumerate(numeric_cols):
            if i < len(axes):
                self.processed_df[col].hist(bins=30, ax=axes[i])
                axes[i].set_title(f'Distribution of {col}')
                axes[i].set_xlabel(col)
                axes[i].set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig('plots/feature_distributions.png')
        plt.close()
        
        # Time series trends if timestamp exists
        timestamp_cols = [col for col in self.processed_df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if timestamp_cols and len(self.processed_df) > 100:
            timestamp_col = timestamp_cols[0]
            
            # Sample data for plotting (every nth point to avoid overcrowding)
            sample_size = min(1000, len(self.processed_df))
            step = len(self.processed_df) // sample_size
            sampled_df = self.processed_df.iloc[::step]
            
            plt.figure(figsize=(15, 8))
            
            # Plot temperature if exists
            if 'temperature' in sampled_df.columns:
                plt.subplot(2, 2, 1)
                plt.plot(sampled_df[timestamp_col], sampled_df['temperature'])
                plt.title('Temperature Over Time')
                plt.xlabel('Time')
                plt.ylabel('Temperature')
                plt.xticks(rotation=45)
            
            # Plot humidity if exists
            if 'humidity' in sampled_df.columns:
                plt.subplot(2, 2, 2)
                plt.plot(sampled_df[timestamp_col], sampled_df['humidity'])
                plt.title('Humidity Over Time')
                plt.xlabel('Time')
                plt.ylabel('Humidity')
                plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig('plots/time_series_trends.png')
            plt.close()
        
        print("EDA completed! Plots saved in 'plots' directory.")
        
        return correlation_matrix
    
    def determine_problem_type(self):
        """Determine the ML problem type based on data characteristics"""
        print("\n" + "=" * 50)
        print("STEP 5: PROBLEM TYPE ANALYSIS")
        print("=" * 50)
        
        # Analyze data to determine problem type
        numeric_cols = self.processed_df.select_dtypes(include=[np.number]).columns
        
        # Check if we have a clear target variable
        potential_targets = ['temperature', 'temp', 'air_quality', 'quality', 'status']
        target_found = False
        
        for target in potential_targets:
            matching_cols = [col for col in numeric_cols if target.lower() in col.lower()]
            if matching_cols:
                self.target_column = matching_cols[0]
                target_found = True
                print(f"Found potential target: {self.target_column}")
        
        # Since we have time series data but no explicit target, we'll predict temperature
        if not target_found:
            temp_cols = [col for col in numeric_cols if 'temp' in col.lower()]
            if temp_cols:
                self.target_column = 'DHT Temp (C)'  # Use DHT temperature as target
                print(f"Using {self.target_column} as target for temperature prediction")
                target_found = True
        
        if target_found:
            print("PROBLEM TYPE: Time-Series Regression (Temperature Forecasting)")
            print("Justification:")
            print("- Dataset has timestamp information")
            print("- Temperature is a continuous variable")
            print("- We can predict future temperature based on historical patterns")
            print("- Time-series features have been engineered")
            return "regression"
        else:
            print("PROBLEM TYPE: Anomaly Detection")
            print("Justification:")
            print("- No clear target variable found")
            print("- Unsupervised learning approach needed")
            print("- Isolation Forest suitable for IoT sensor anomaly detection")
            return "anomaly"
    
    def select_and_compare_models(self, problem_type):
        """Step 6: Model Selection and Comparison"""
        print("\n" + "=" * 50)
        print("STEP 6: MODEL SELECTION AND COMPARISON")
        print("=" * 50)
        
        # Prepare features
        numeric_cols = self.processed_df.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols if col != self.target_column]
        
        # Remove date/time columns from features
        feature_cols = [col for col in feature_cols if 'date' not in col.lower() and 'time' not in col.lower()]
        self.feature_columns = feature_cols
        
        X = self.processed_df[feature_cols]
        y = self.processed_df[self.target_column] if self.target_column else None
        
        # Split data
        if y is not None:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        else:
            X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"Training set size: {len(X_train)}")
        print(f"Test set size: {len(X_test)}")
        print(f"Number of features: {len(feature_cols)}")
        
        if problem_type == "regression":
            models = {
                'Linear Regression': LinearRegression(),
                'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'XGBoost': None  # Will add if available
            }
            
            results = {}
            
            for name, model in models.items():
                print(f"\nTraining {name}...")
                
                if name == 'Linear Regression':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    mae = mean_absolute_error(y_test, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    r2 = r2_score(y_test, y_pred)
                    
                    results[name] = {'MAE': mae, 'RMSE': rmse, 'R2': r2}
                    print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
                
                elif name == 'Random Forest':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    mae = mean_absolute_error(y_test, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    r2 = r2_score(y_test, y_pred)
                    
                    results[name] = {'MAE': mae, 'RMSE': rmse, 'R2': r2}
                    print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
            
            # Select best model
            best_model_name = min(results.keys(), key=lambda x: results[x]['RMSE'])
            print(f"\n🏆 Best Model: {best_model_name}")
            print(f"Performance: {results[best_model_name]}")
            
            # Train final model
            if best_model_name == 'Random Forest':
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            else:
                self.model = LinearRegression()
            
            self.model.fit(X_train_scaled, y_train)
            
            return results
        
        else:  # Anomaly Detection
            print("Training Isolation Forest for Anomaly Detection...")
            
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(X_train_scaled)
            
            # Get anomaly scores
            y_pred_train = self.model.predict(X_train_scaled)
            y_pred_test = self.model.predict(X_test_scaled)
            
            anomaly_scores_train = self.model.decision_function(X_train_scaled)
            anomaly_scores_test = self.model.decision_function(X_test_scaled)
            
            print(f"Training anomalies detected: {sum(y_pred_train == -1)}/{len(y_pred_train)}")
            print(f"Test anomalies detected: {sum(y_pred_test == -1)}/{len(y_pred_test)}")
            print(f"Average anomaly score (train): {np.mean(anomaly_scores_train):.4f}")
            print(f"Average anomaly score (test): {np.mean(anomaly_scores_test):.4f}")
            
            return {'Isolation Forest': 'Anomaly Detection Model Trained'}
    
    def model_explainability(self):
        """Step 7: Model Explainability"""
        print("\n" + "=" * 50)
        print("STEP 7: MODEL EXPLAINABILITY")
        print("=" * 50)
        
        if hasattr(self.model, 'feature_importances_'):
            # Get feature importances
            importances = self.model.feature_importances_
            feature_importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            print("Top 10 Most Important Features:")
            print(feature_importance_df.head(10))
            
            # Plot feature importance
            plt.figure(figsize=(12, 8))
            top_features = feature_importance_df.head(15)
            plt.barh(range(len(top_features)), top_features['importance'])
            plt.yticks(range(len(top_features)), top_features['feature'])
            plt.xlabel('Feature Importance')
            plt.title('Top 15 Feature Importances')
            plt.tight_layout()
            plt.savefig('plots/feature_importance.png')
            plt.close()
            
            print("Feature importance plot saved to 'plots/feature_importance.png'")
            
            return feature_importance_df
        else:
            print("Model does not support feature importance analysis")
            return None
    
    def save_model(self):
        """Step 8: Save Model and Preprocessing Pipeline"""
        print("\n" + "=" * 50)
        print("STEP 8: SAVING MODEL AND PIPELINE")
        print("=" * 50)
        
        # Create model directory if it doesn't exist
        os.makedirs('saved_models', exist_ok=True)
        
        # Save the trained model
        model_path = 'saved_models/climascope_model.pkl'
        joblib.dump(self.model, model_path)
        print(f"Model saved to: {model_path}")
        
        # Save the scaler
        if self.scaler:
            scaler_path = 'saved_models/preprocessor.pkl'
            joblib.dump(self.scaler, scaler_path)
            print(f"Preprocessor saved to: {scaler_path}")
        
        # Save feature columns
        feature_path = 'saved_models/feature_columns.pkl'
        joblib.dump(self.feature_columns, feature_path)
        print(f"Feature columns saved to: {feature_path}")
        
        # Save target column if exists
        if self.target_column:
            target_path = 'saved_models/target_column.pkl'
            joblib.dump(self.target_column, target_path)
            print(f"Target column saved to: {target_path}")
        
        print("✅ Model and pipeline saved successfully!")
        
        return {
            'model_path': model_path,
            'scaler_path': scaler_path if self.scaler else None,
            'feature_path': feature_path,
            'target_path': target_path if self.target_column else None
        }

def main():
    """Main function to run the complete ML pipeline"""
    print("🌡️  ClimaScope ML Pipeline Starting...")
    
    # Initialize the ML pipeline
    data_path = r"D:\climascope\sensor_data.xlsx"
    ml_pipeline = ClimaScopeML(data_path)
    
    try:
        # Step 1: Load and inspect data
        df = ml_pipeline.load_and_inspect_data()
        
        # Step 2: Preprocess data
        processed_df = ml_pipeline.preprocess_data()
        
        # Step 3: Feature engineering
        featured_df = ml_pipeline.feature_engineering()
        
        # Step 4: Exploratory data analysis
        correlation_matrix = ml_pipeline.exploratory_data_analysis()
        
        # Step 5: Determine problem type
        problem_type = ml_pipeline.determine_problem_type()
        
        # Step 6: Model selection and comparison
        model_results = ml_pipeline.select_and_compare_models(problem_type)
        
        # Step 7: Model explainability
        feature_importance = ml_pipeline.model_explainability()
        
        # Step 8: Save model and pipeline
        saved_paths = ml_pipeline.save_model()
        
        print("\n" + "=" * 50)
        print("� CLIMASCOPE ML PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("Summary:")
        print(f"- Problem Type: {problem_type}")
        print(f"- Model Performance: {model_results}")
        print(f"- Model saved to: {saved_paths['model_path']}")
        print(f"- Preprocessor saved to: {saved_paths['scaler_path']}")
        print("\nNext steps: FastAPI integration and frontend updates")
        
    except Exception as e:
        print(f"❌ Error in pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()
