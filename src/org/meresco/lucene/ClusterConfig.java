package org.meresco.lucene;

import java.util.ArrayList;
import java.util.List;

import javax.json.JsonArray;
import javax.json.JsonObject;


public class ClusterConfig {
	public double clusteringEps;
	public int clusteringMinPoints;
	public int clusterMoreRecords;
	public List<ClusterField> clusterFields;
	
	private ClusterConfig() {
	}
	
	public ClusterConfig(double clusteringEps, int clusteringMinPoints, int clusterMoreRecords) {
		this.clusteringEps = clusteringEps;
		this.clusteringMinPoints = clusteringMinPoints;
		this.clusterMoreRecords = clusterMoreRecords;
		this.clusterFields = new ArrayList<>();
	}
	
	public static ClusterConfig parseFromJsonObject(JsonObject jsonObject) {
		ClusterConfig clusterConfig = new ClusterConfig();
        for (String key : jsonObject.keySet()) {
            switch (key) {
            case "clusteringEps":
            	clusterConfig.clusteringEps = jsonObject.getJsonNumber(key).doubleValue();
                break;
            case "clusteringMinPoints":
            	clusterConfig.clusteringMinPoints = jsonObject.getInt(key);
                break;
            case "clusterMoreRecords":
            	clusterConfig.clusterMoreRecords  = jsonObject.getInt(key);
                break;
            case "clusterFields":
            	clusterConfig.clusterFields = parseClusterFields(jsonObject.getJsonArray(key));
                break;
            }
        }
        return clusterConfig;
	}
	
    private static List<ClusterField> parseClusterFields(JsonArray jsonClusterFields) {
        List<ClusterField> clusterFields = new ArrayList<ClusterField>();
        for (int i=0; i<jsonClusterFields.size(); i++) {
            JsonObject clusterField = jsonClusterFields.getJsonObject(i);
            String filterValue = clusterField.getString("filterValue", null);
            clusterFields.add(new ClusterField(clusterField.getString("fieldname"), clusterField.getJsonNumber("weight").doubleValue(), filterValue));
        }
        return clusterFields;
    }
    
    
	public static class ClusterField {
	    public String fieldname;
	    public double weight;
	    public String filterValue;
	
	    public ClusterField(String fieldname, double weight, String filterValue) {
	        this.fieldname = fieldname;
	        this.weight = weight;
	        this.filterValue = filterValue;
	    }
	}
}