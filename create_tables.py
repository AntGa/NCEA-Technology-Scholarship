import mysql.connector

connector = mysql.connector.connect(
    host="localhost",
    user="root",
    password="inventory001",
    database="inventorydatabase"
) 


#cur.execute("CREATE TABLE user_table (username VARCHAR(255), password VARCHAR(255), email_address VARCHAR(255), userID int PRIMARY KEY AUTO_INCREMENT)") 
#mysql.connection.commit()  

#cur2= connector.cursor()'
#cur2.execute("CREATE TABLE sales (saleName VARCHAR(255), password VARCHAR(255), email_address VARCHAR(255), userID int PRIMARY KEY AUTO_INCREMENT)")

#cur = connector.cursor()
#cur.execute("CREATE TABLE Locations (locationName VARCHAR(50), username VARCHAR(50), locationID int PRIMARY KEY AUTO_INCREMENT)")



#CREATE TABLE `products` (
  #`name` varchar(50) DEFAULT NULL,
  #`price` decimal(19,2) NOT NULL,
  #`quantity` smallint unsigned DEFAULT NULL,
  #`description` varchar(250) DEFAULT NULL,
 # `productID` int NOT NULL AUTO_INCREMENT,
 # `username` varchar(45) NOT NULL,
 # `datetime` varchar(45) DEFAULT NULL,
 # `updatetime` varchar(45) DEFAULT NULL,
 # `location` varchar(255) DEFAULT NULL,
 # PRIMARY KEY (`productID`)
#) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `locations` (
  `locationName` varchar(50) DEFAULT NULL,
  `username` varchar(50) DEFAULT NULL,
  `locationID` int NOT NULL AUTO_INCREMENT,
  `locationDesc` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`locationID`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `sales` (
  `saleName` varchar(255) NOT NULL,
  `salePrice` decimal(19,2) NOT NULL,
  `saleQuantity` smallint unsigned NOT NULL,
  `saleDescription` varchar(255) DEFAULT NULL,
  `saleID` int unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(45) DEFAULT NULL,
  `datetime` varchar(45) DEFAULT NULL,
  `updatetime` varchar(45) DEFAULT NULL,
  `location` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`saleID`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `usertable` (
  `username` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `emailaddress` varchar(255) DEFAULT NULL,
  `userID` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
