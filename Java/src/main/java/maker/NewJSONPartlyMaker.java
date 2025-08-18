package maker;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintStream;
import java.util.List;

import com.google.gson.JsonObject;

import functional.classes.Route;
import visual.Console;
import visual.MenuInitializer;

public class NewJSONPartlyMaker {
	public static Console console = MenuInitializer.console;
	public static PrintStream stream = new PrintStream(console);
	
	public static void settingFile( String folder, String routeType) {
        try (FileWriter file = new FileWriter(folder + "/" + routeType + ".json")) {
            file.write("{");
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
	
	public static void jsonToFile(List<Route> routes,String folder, String routeType, boolean isFirstVertex) {
                   
        try (FileWriter file = new FileWriter(folder + "/" + routeType + ".json",true)) {
        	 for (int i = 0; i < routes.size(); i++) {
                 Route route = routes.get(i);
                 JsonObject object = new JsonObject();
                 int id = route.getFrom() * 10000 + route.getTo();
                 object.addProperty("from", route.getFrom());
                 object.addProperty("to", route.getTo());
                 object.addProperty("price", (int)route.getEuro_price());
                 object.addProperty("duration", route.getTrip_duration());
                 object.addProperty("direct_routes", route.getTravel_data());
                 file.write(",");
                 file.write("\"" + id + "\":");
                 file.write(object.toString());
//                 if(!(route.equals(routes.get(routes.size()-1)) && isLastVertex)) {
//                 	file.write(",");
//                 }       
                 file.flush();
                 
             }
            
            //stringMaker(filename + ".json created");
        } catch (IOException e) {
            e.printStackTrace();
        }
        
        if(isFirstVertex) {
        	readFixAndWrite(folder,routeType);
        }
		
	}
	
	private static void readFixAndWrite(String folder, String routeType) {
		String str = "";
		try (FileReader fileRead = new FileReader(folder + "/" + routeType + ".json");
				){
			int character;
            StringBuilder contentBuilder = new StringBuilder();

            // Read characters until end of file
            while ((character = fileRead.read()) != -1) {
                contentBuilder.append((char) character);
            }
            str = contentBuilder.toString();
            str = str.replaceFirst(",", "");
            
		} 
		catch (IOException e) {
            e.printStackTrace();
        }
		try(FileWriter fileWrite = new FileWriter(folder + "/" + routeType + ".json")){
			fileWrite.write(str);
            fileWrite.flush();
		}catch (IOException e) {
            e.printStackTrace();
        }
	}
	
	public static void endingFile( String folder, String routeType) {
        try (FileWriter file = new FileWriter(folder + "/" + routeType + ".json",true)) {
            file.write("}");
            file.flush();
            stringMaker(routeType + ".json created");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
	
	public static void stringMaker (String input) {
        System.out.println(input);
        stream.println(input);
    }

}
