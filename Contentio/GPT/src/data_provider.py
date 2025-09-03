import polars as pl
from typing import Generator, Union
from pathlib import Path


# This class is likely a provider or generator of city and country information
class CSVDataProvider:
    def __init__(self, path: str='../files/csv/cities_countries.csv') -> None:
        """
        This is the constructor method of a class. It takes a path parameter as input which is a string representing the path of a CSV file. The method reads the CSV file using polars library's read_csv method and stores it in a variable called df. It also initializes a variable called numrows with the number of rows in the CSV file.

        Args:
            path (str): string representing the path to a CSV file containing data
        """
        try:
            self.path = Path(path)
            self.df = pl.read_csv(self.path)
            self.numrows = self.df.shape[0]
            
        except FileNotFoundError:
            print("File not found: ", path)
        except PermissionError:
            print("Permission denied to access file: ", path)   
        except IsADirectoryError:
            print("The specified path is a directory: ", path)
        except UnicodeDecodeError:
            print("Error decoding the CSV file due to encoding issues: ", path)    
        except pl.NoDataError:
            print("The file is empty or contains no data: ", path)   
        except pl.ParserError:
            print("Error parsing the CSV file: ", path)    
        except pl.EncodingError:
            print("Error decoding the CSV file due to encoding issues: ", path)   
        except ValueError as e:
            print("ValueError: ", e)
            
    
    def gen_data(self,
                      from_: int=0, 
                      to_: int=-1, 
                      type_: list=['city', 'country'], 
                      sort_: str='city') -> Generator[tuple,
                                                        Union[int, list[str], str], 
                                                        pl.ColumnNotFoundError]:
        """
        This is a method that generates a tuples of values from certain columns. The parameters include the range of values to generate, the type of data to include (city and/or country), and how to sort the values. The method uses a polars dataframe to retrieve the data and returns a generator object that yields the desired values.

        Args:
            from_ (int, optional): the first element of the returned subset. Defaults to 0.
            to_ (int, optional): the last element of the returned subset. Defaults to 0.
            type_ (list, optional): list of column names whose values are returned. Defaults to ['city', 'country'].
            sort_ (str, optional): the name of the column to sort by. Defaults to 'city'.

        Yields:
            Generator[tuple, int, AttributeError]: tuples generator
        """
        if to_ == -1: to_ = self.numrows
        for value in self.df[type_].sort(sort_).rows()[from_:to_]:
            yield value
            
    
    def get_city_name(self, id: int) -> str:
        """
        Takes an integer id as input and returns the corresponding city name from the dataframe 'df_cities_countries'. It filters the dataframe based on the id and returns the first value of the 'city' column.

        Args:
            id (int): city id

        Returns:
            str: city name
        """
        return self.df.filter(pl.col('id_city') == id)['city'][0]
    
    
    def get_city_id(self, name: str) -> int:
        """
        This function takes in a city name as a string and returns the corresponding city ID as an integer. It does this by filtering the dataframe of cities and countries for the row where the 'city' column matches the input name, and then returning the value in the 'id_city' column for that row. 

        Args:
            name (str): city name

        Returns:
            int: city id
        """
        return self.df.filter(pl.col('city') == name)['id_city'][0]
        
    
    def get_numrows(self):
        return self.numrows
    
    
    def get_columns(self):
        return self.df.columns
    

if __name__ == '__main__':
    # dp = CSVDataProvider()
    # for d in dp.gen_data():
    #     print(d)
    # print(dp.get_city_name(200))
    # print(dp.get_city_id('London'))
    # print(dp.get_columns())
    pass