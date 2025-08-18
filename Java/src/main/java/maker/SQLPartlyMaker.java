package maker;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintStream;
import java.util.List;

import functional.classes.Route;
import functional.classes.TravelData;
import visual.Console;
import visual.MenuInitializer;

public class SQLPartlyMaker {
	public static Console console = MenuInitializer.console;
    public static PrintStream stream = new PrintStream(console);
	
	public static void settingFile( String folder, String routeType) {
		
		String result = "DROP TABLE IF EXISTS " + routeType + ";" + "\n" +
                "CREATE TABLE " + routeType + "\n" +
                "(" + "\n" +
                "   id                  INT                 NOT NULL," + "\n" +
                "   `from`              INT                 NOT NULL," + "\n" +
                "   `to`                INT                 NOT NULL," + "\n" +
                "   euro_price          FLOAT               NOT NULL," + "\n" +
                "   trip_duration       INT                 NOT NULL," + "\n" +
                "   travel_data         VARCHAR(255)        NOT NULL," + "\n" +
                "PRIMARY KEY (id)" + "\n" +
                ") ENGINE = InnoDB" + "\n" +
                "DEFAULT CHARSET = utf8;" + "\n" +
                "LOCK TABLES " + routeType + " WRITE;" + "\n";
		result += "INSERT INTO " + routeType + " (id, `from`,`to`, euro_price, trip_duration, travel_data) " +
                "VALUES";
		
        try (FileWriter file = new FileWriter(folder + "/" + routeType + ".sql")) {
            file.write(result);
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
	
	public static void routesSQL(List<Route> routes,String folder, String routeType, boolean isFirstVertex) {
		String result = "";
		for (int i = 0; i < routes.size(); i++) {
            Route route = routes.get(i);
            result += ",\n";
            result = result + "(" + route.getId() + "," +
                    route.getFrom() + "," +
                    route.getTo() + "," +
                    route.getEuro_price() + "," +
                    route.getTrip_duration() + ",'" +
                    route.getTravel_data() + "')";
//            if (i == routes.size() - 1 && isLastVertex) {
//            	result = result + ";\n";
//            } else {
//            	result = result + ",\n";
//            }
        }
		
		try (FileWriter file = new FileWriter(folder + "/" + routeType + ".sql",true)) {
            file.write(result);
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
		if (isFirstVertex) {
			readFixAndWrite(folder,routeType);
		}
	}
	
	private static void readFixAndWrite(String folder, String routeType) {
		String str = "";
		try (FileReader fileRead = new FileReader(folder + "/" + routeType + ".sql")){
			int character;
            StringBuilder contentBuilder = new StringBuilder();

            // Read characters until end of file
            while ((character = fileRead.read()) != -1) {
                contentBuilder.append((char) character);
            }
            str = contentBuilder.toString();
            str = str.replaceFirst("VALUES,", "VALUES \n");
            
		} 
		catch (IOException e) {
            e.printStackTrace();
        }
		try(FileWriter fileWrite = new FileWriter(folder + "/" + routeType + ".sql")){
			fileWrite.write(str);
            fileWrite.flush();
		}catch (IOException e) {
            e.printStackTrace();
        }
	}
	
	public static void endingFile(String folder, String routeType) {
		String result = ";\n UNLOCK TABLES;";
		
		try (FileWriter file = new FileWriter(folder + "/" + routeType + ".sql",true)) {
            file.write(result);
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
		stringMaker(routeType + ".sql created");
	}
	
	public static void outputIntoTravelDataFile( List<TravelData> travelData, String folder) {
		settingTravelDataFile(folder);
		travelDataToFile(folder, travelData);
		endingTravelDataFile(folder);
	}
	
	public static void settingTravelDataFile(String folder) {
		String result = "DROP TABLE IF EXISTS travel_data;" + "\n" +
                "CREATE TABLE travel_data" + "\n" +
                "(" + "\n" +
                "   id                  INT                 NOT NULL," + "\n" +
                "   `from`              INT                 NOT NULL," + "\n" +
                "   `to`                INT                 NOT NULL," + "\n" +
                "   transportation_type INT                 NOT NULL," + "\n" +
                "   euro_price          FLOAT               NOT NULL," + "\n" +
                "   time_in_minutes     INT                 NOT NULL," + "\n" +
                "PRIMARY KEY (id)" + "\n" +
                ") ENGINE = InnoDB" + "\n" +
                "DEFAULT CHARSET = utf8;" + "\n" +
                "LOCK TABLES travel_data WRITE;" + "\n";
		result += "INSERT INTO travel_data (id, `from`,`to`, transportation_type, euro_price, time_in_minutes) " +
                "VALUES " + "\n";
		
		try (FileWriter file = new FileWriter(folder + "/" + "travel_data.sql")) {
            file.write(result);
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
	}
	
	public static void travelDataToFile(String folder, List<TravelData> travelData) {
		try (FileWriter file = new FileWriter(folder + "/" + "travel_data.sql",true)) {
			
			for (int i = 0; i < travelData.size(); i++) {
	            TravelData data = travelData.get(i);
	            String result = "(" + data.getId() + "," +
	                    data.getFrom() + "," +
	                    data.getTo() + "," +
	                    data.getTransportation_type() + "," +
	                    data.getEuro_price() + "," +
	                    data.getTime_in_minutes() + ")";
	            if (i < travelData.size() - 1) {
	                result = result + ",\n";
	            } else {
	                result = result + ";\n";
	            }
	            file.write(result);
	            file.flush();
	        }			            
        } catch (IOException e) {
            e.printStackTrace();
        }
	}
	
	public static void endingTravelDataFile(String folder) {
		String result ="UNLOCK TABLES;";
		try (FileWriter file = new FileWriter(folder + "/" + "travel_data.sql",true)) {
            file.write(result);
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
		stringMaker("travel_data.sql created");
	}
	
	 public static void stringMaker (String input) {
	        System.out.println(input);
	        stream.println(input);
	    }

}
