-- MySQL dump 10.13  Distrib 8.0.39, for Linux (x86_64)
--
-- Host: localhost    Database: whiplano
-- ------------------------------------------------------
-- Server version	8.0.39-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--

-- Table structure for table `collections`
--
USE whiplano
DROP TABLE IF EXISTS `collections`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `collections` (
  `trs_id` varchar(255) NOT NULL,
  `collection_name` varchar(255) NOT NULL,
  `mint_address` varchar(255) NOT NULL,
  `token_account_address` varchar(255) DEFAULT NULL,
  `creator_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`trs_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `collections`
--

LOCK TABLES `collections` WRITE;
/*!40000 ALTER TABLE `collections` DISABLE KEYS */;
INSERT INTO `collections` VALUES ('109644570642593598123547152550654533752','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('116560632333623928767952484789278288207','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('13241861340234348097525001180053051152','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('140078347205932935002490706156373453097','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('16879342676176644148559919097531007678','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('239805249148134425865073013715181610103','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('273125618343484859138792576554427540356','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('285352582812040577080029455555801870910','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('339802020199894809085529781202049654892','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('82807287687901696395139357456516521470','MintingTrs22','9eNaqVuLp4xz3MU2eomXoqoKmUZHCgDjpM9pNdpv83Dk',NULL,'f02b21ec-dcaa-449a-9107-f38bad40bbfe');
/*!40000 ALTER TABLE `collections` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paypal_transactions`
--

DROP TABLE IF EXISTS `paypal_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paypal_transactions` (
  `transaction_id` varchar(255) NOT NULL,
  `buyer_id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `transaction_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('created','executed','confirmed') DEFAULT 'created',
  PRIMARY KEY (`transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paypal_transactions`
--

LOCK TABLES `paypal_transactions` WRITE;
/*!40000 ALTER TABLE `paypal_transactions` DISABLE KEYS */;
/*!40000 ALTER TABLE `paypal_transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `transaction_number` int NOT NULL,
  `collection_name` varchar(255) NOT NULL,
  `buyer_id` varchar(255) NOT NULL,
  `seller_id` varchar(255) NOT NULL,
  `transaction_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `cost` decimal(10,2) NOT NULL,
  `number` int NOT NULL,
  `status` enum('initiated','approved','finished') DEFAULT 'initiated',
  `buyer_transaction_id` varchar(255) NOT NULL,
  PRIMARY KEY (`transaction_number`),
  KEY `fk_buyer_id` (`buyer_id`),
  KEY `fk_seller_id` (`seller_id`),
  CONSTRAINT `fk_buyer_id` FOREIGN KEY (`buyer_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_seller_id` FOREIGN KEY (`seller_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trs`
--

DROP TABLE IF EXISTS `trs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trs` (
  `user_id` varchar(255) DEFAULT NULL,
  `trs_id` varchar(255) NOT NULL,
  `collection_name` varchar(255) DEFAULT NULL,
  `acquired_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `creator` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`trs_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trs`
--

LOCK TABLES `trs` WRITE;
/*!40000 ALTER TABLE `trs` DISABLE KEYS */;
INSERT INTO `trs` VALUES ('f02b21ec-dcaa-449a-9107-f38bad40bbfe','109644570642593598123547152550654533752','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','116560632333623928767952484789278288207','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','13241861340234348097525001180053051152','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','140078347205932935002490706156373453097','MintingTrs22','2024-09-21 04:25:22','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','16879342676176644148559919097531007678','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','239805249148134425865073013715181610103','MintingTrs22','2024-09-21 04:25:22','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','273125618343484859138792576554427540356','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','285352582812040577080029455555801870910','MintingTrs22','2024-09-21 04:25:22','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','339802020199894809085529781202049654892','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe'),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','82807287687901696395139357456516521470','MintingTrs22','2024-09-21 04:25:21','f02b21ec-dcaa-449a-9107-f38bad40bbfe');
/*!40000 ALTER TABLE `trs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` varchar(255) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('36479dd4-36aa-4bb1-9804-114d7a070670','dummyartisan','sb-v8uvt32804992@personal.example.com','$2b$12$aHg6yh5Xz5zxOeK.yiH/beG4mmxmINbTJDsDHUwJiQb3akNuuaZHq','2024-09-19 19:09:29',NULL),('6e53fa4d-aada-41d6-abd9-78905344a592','dummybuyer','sb-qxw47c32804983@personal.example.com','$2b$12$9e/T5i3S5AXZPtdzHYvXReBQCaIBqGOZJ7dQJz11pbhlidXj2dE6e','2024-09-19 19:09:11',NULL),('f02b21ec-dcaa-449a-9107-f38bad40bbfe','dummycreator','sb-yifau32804991@personal.example.com','$2b$12$Q8qkclB0b4FJwenZZM0MPuLv8m9MR.YdABH4SjGTGyGvt6.iaaG52','2024-09-19 19:08:05',NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-09-21 10:17:54
