package code;

public class Product {

    int i;
    String name;
    double price;
    String desc;

    public Product(int i, String name, double price, String desc) {
        this.i = i;
        this.name = name;
        this.price = price;
        this.desc = desc;
    }
         

    // add getters and setters
    public int getI() {
        return i;
    }
    public void setI(int i) {
        this.i = i;
    }
    public String getName() {
        return name;
    }
    public void setName(String name) {
        this.name = name;
    }
    public double getPrice() {
        return price;
    }
    public void setPrice(double price) {
        this.price = price;
    }
    public String getDesc() {
        return desc;
    }
    public void setDesc(String desc) {
        this.desc = desc;
    }
}
