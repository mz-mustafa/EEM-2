import pandas as pd
import random
from project import Project

class Source:
    def __init__(self, name, attributes, units, values, start_year, rating, rating_unit,reserve_perc,priority):
        self.name = name
        # Combine attributes and units for more comprehensive information
        self.metadata = {attr: {'unit': unit, 'value': value} for attr, unit, value in zip(attributes, units, values)}
        self.ops_data = self._initialize_years()
        self.config = {
            'start_year' : start_year,
            'rating' : rating,
            'rating_unit' : rating_unit,
            'reserve_perc' : reserve_perc,
            'priority' : priority
        }
        
    
    def display_info(self):
        for attr, info in self.data.items():
            print(f"{attr} ({info['unit']}): {info['value']}")

    def _initialize_years(self):
        # Initialize yearly data structure
        years_data = {}
        for year in range(1, 13):  # For each of the 12 years
            years_data[year] = {
                'year_potential_failures': 0,
                'year_failures_mitigated': 0,
                'year_downtime': 0,
                'year_energy_output': 0,
                'year_cost_of_operation': 0,
                'year_fuel_cost': 0,
                'year_fixed_opex': 0,
                'year_var_opex': 0,
                'year_depreciation': 0,
                'year_ppa_cost': 0,
                'year_operation_hours': 0,
                'months': self._initialize_months()
            }
        return years_data
    
    def _initialize_months(self):
        # Initialize monthly data structure within each year
        months_data = {}
        for month in range(1, 13):  # 12 months
            months_data[month] = {
                'month_potential_failures': 0,
                'month_failures_mitigated': 0,
                'month_downtime': 0,
                'month_energy_output': 0,
                'month_cost_of_operation': 0,
                'month_fuel_cost': 0,
                'month_fixed_opex': 0,
                'month_var_opex': 0,
                'month_depreciation': 0,
                'month_ppa_cost': 0,
                'month_operation_hours': 0,
                'days': self._initialize_days(month)
            }
        return months_data
    
    def _initialize_days(self, month):
        # Determine the correct number of days for each month
        if month == 2:  # February
            days_in_month = 28
        elif month in [4, 6, 9, 11]:  # April, June, September, November
            days_in_month = 30
        else:  # All other months
            days_in_month = 31

        days_data = {}
        for day in range(1, days_in_month + 1):
            days_data[day] = {
                'avg_power_output': 0,
                'min_power_output': 0,
                'max_power_output': 0,
                'day_energy_output': 0,
                'failure_occurrence': 0,
                'failure_mitigation': 0,
                'pperation_hours': 0,
                'downtime': 0,
                'hours': self._initialize_hours()
            }
        return days_data
    
    def _initialize_hours(self):
        # Initialize hourly data structure within each day
        hours_data = {}
        for hour in range(24):  # 24 hours
            hours_data[hour] = {
                'power_capacity': 0,
                'power_output': 0,
                'energy_output': 0,
                'status': ''
            }
        return hours_data

    def seed_availabilty(self):
        for year, year_data in self.ops_data.items():
            days_of_year = []
            # Generate a flat list of all day-hour combinations
            for month, month_data in year_data['months'].items():
                for day, day_data in month_data['days'].items():
                    for hour in range(24):
                        days_of_year.append((month, day, hour))
            
            # Randomly select days for failures, ensuring unique days
            failure_days = random.sample(days_of_year, self.metadata['num_annual_fails']['value'])

            for month, day, fail_hour in failure_days:
                # Mark the failure hour
                year_data['months'][month]['days'][day]['Hours'][fail_hour]['Status'] = -2
                
                # Apply downtime for subsequent hours
                downtime = self.metadata['downtime_per_fail']['value'] - 1
                while downtime > 0:
                    fail_hour += 1
                    if fail_hour >= 24:
                        fail_hour = 0
                        day += 1
                        # Move to the next month if the days exceed the month's length
                        if day > len(year_data['months'][month]['days']):
                            day = 1
                            month += 1
                            # Reset to January if the month exceeds the year
                            if month > 12:
                                month = 1
                    year_data['months'][month]['days'][day]['Hours'][fail_hour]['Status'] = -1
                    downtime -= 1
        self.aggregate_availability()

    def aggregate_availability(self):
        # Iterate through all levels of data to update day, month, and year aggregates
        for year, year_data in self.ops_data.items():
            for month, month_data in year_data['months'].items():
                for day, day_data in month_data['days'].items():
                    # Count the failure occurrences and downtime at the day level
                    failure_occurrence = sum(1 for hour in day_data['Hours'].values() if hour['Status'] == -2)
                    downtime = sum(1 for hour in day_data['Hours'].values() if hour['Status'] == -1) + failure_occurrence
                    
                    # Update day level data
                    day_data['Failure_occurrence'] = failure_occurrence
                    day_data['Downtime'] = downtime
                    
                    # Accumulate counts for the month level data
                    month_data['month_potential_failures'] += failure_occurrence
                    month_data['month_downtime'] += downtime
                
                # Accumulate counts for the year level data
                year_data['year_potential_failures'] += month_data['month_potential_failures']
                year_data['year_downtime'] += month_data['month_downtime']   

    def power_capacity(self,yr,mon,day,hr):
        
        #the way power output is calculated will be based on the src type

        #for captive it will be capacity consider. degradation per year and also reserve_perc
        
        #we will need to add fields like units in operation to hour level dicts to capture captive spin reserve and assoc costs
        
        #for thermal ppa it will be mainly output capacity

        #for solar it will be based on time of day and will need to use Project data

        return True

class SourceManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.sources = {}
        try:
            self.read_sources()
        except Exception as e:
            print(f"Failed to load source data: {e}")
            raise

    def read_sources(self):
        df = pd.read_excel(self.file_path, sheet_name='src_ppa')
        
        # Read the first set of attribute names and units
        attributes_1 = df['B'][1:18].tolist()  # Adjust based on actual data range
        units_1 = df['C'][1:18].tolist()

        # Process sources from the first range (D2 and rightwards)
        self._process_source_range(df, attributes_1, units_1, start_col=3, name_row=0, data_start_row=1)

        # Read the second set of attribute names and units
        attributes_2 = df['J'][1:19].tolist()  # Adjust for the new range
        units_2 = df['K'][1:19].tolist()

        # Process sources from the second range (L2 and rightwards)
        self._process_source_range(df, attributes_2, units_2, start_col=11, name_row=0, data_start_row=1)

    def _process_source_range(self, df, attributes, units, start_col, name_row, data_start_row):
        # Iterate over columns starting from the specified start_col
        for col_idx, col in enumerate(df.columns[start_col:], start=start_col):
            # Check if the column header is a non-empty string (indicating a source type)
            if pd.isnull(df.iloc[name_row, col_idx]):
                break  # Stop if a blank source type is found
            name = df.iloc[name_row, col_idx]
            values = df.iloc[data_start_row:data_start_row+len(attributes), col_idx].tolist()
            self.sources[name] = Source(name, attributes, units, values)

    def get_source_by_name(self, name):
        return self.sources.get(name)
    
    def select_sources(source_manager):
        print("Available sources:")
        for name in source_manager.sources.keys():
            print(name)
        
        selected_sources = []
        while True:
            choice = input("Enter source name to select (or 'done' to finish): ")
            if choice == 'done':
                break
            if choice in source_manager.sources:
                config = collect_source_config()
                source_instance = Source(choice, **source_manager.sources[choice].metadata, config=config)
                selected_sources.append(source_instance)
            else:
                print("Source not found.")
        return selected_sources

def collect_source_config():
    # Collect configuration data from the user
    # This is a placeholder; implement according to your application's needs
    return {
        'start_year': input("Start Year: "),
        'rating': input("Rating: "),
        'rating_unit': input("Rating Unit: "),
        'reserve_perc': input("Reserve Percentage: ")
    }
