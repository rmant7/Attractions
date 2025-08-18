package functional.classes;

import org.jgrapht.graph.DefaultWeightedEdge;

public class CheapTripWeightedEdge extends DefaultWeightedEdge {

	/**
	 * 
	 */
	private static final long serialVersionUID = 3176190726547910070L;
	
	private int myId;
	private int duration;
	
	public void setMyId(int id) {
		this.myId = id;
	}
	
	public int getMyId() {
		return this.myId;
	}
	
	@Override
    public String toString()
    {
        return "path id: " + this.myId + " " + "Duration: " + this.duration + " " +  super.toString();
    }

	public int getDuration() {
		return duration;
	}

	public void setDuration(int duration) {
		this.duration = duration;
	}

}
