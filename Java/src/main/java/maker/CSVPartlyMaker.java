package maker;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintStream;

import visual.Console;
import visual.MenuInitializer;

public class CSVPartlyMaker {
	
	public static Console console = MenuInitializer.console;
	public static PrintStream stream = new PrintStream(console);
	
	public static void settingFile( String folder, String routeType) {
		try (FileWriter file = new FileWriter(folder + "/" + routeType + ".csv")) {
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
	}
	
	public static void endingFile(String folder, String routeType) {
		File checkingfile = new File(folder + "/" + routeType + ".csv");
		if (checkingfile.length() > 0) {
			try (FileWriter file = new FileWriter(folder + "/" + routeType + ".csv",true)) {
	            file.write(";");
	            file.flush();
	            stringMaker(routeType + ".csv created");
	        } catch (IOException e) {
	            e.printStackTrace();
	        }
		}      
    }
	
	public static void stringMaker (String input) {
        System.out.println(input);
        stream.println(input);
    }

}
