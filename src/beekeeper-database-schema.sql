CREATE DATABASE beekeeper;
USE beekeeper;

--
-- Table structure for table `area`
--

DROP TABLE IF EXISTS `area`;
CREATE TABLE `area` (
  `name` varchar(45) NOT NULL,
  `city` varchar(45) NOT NULL,
  `region` varchar(45) NOT NULL,
  PRIMARY KEY (`name`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `hive`
--

DROP TABLE IF EXISTS `hive`;
CREATE TABLE `hive` (
  `id` int NOT NULL AUTO_INCREMENT,
  `area_name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hive_id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `measurement`
--

DROP TABLE IF EXISTS `measurement`;
CREATE TABLE `measurement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(45) NOT NULL,
  `value` int NOT NULL,
  `timestamp` timestamp NOT NULL,
  `node_id` varchar(16) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `node`
--

DROP TABLE IF EXISTS `node`;
CREATE TABLE `node` (
  `id` varchar(16) NOT NULL,
  `type` varchar(45) NOT NULL,
  `communication_time` int unsigned,
  `last_communication` timestamp NOT NULL,
  `hive_id` int,
  PRIMARY KEY (`id`),
  UNIQUE KEY `node_id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `actuator_information`
--

CREATE TABLE `actuator_information` (
  `node_id` varchar(16) NOT NULL,
  `coap_ip` varchar(32) NOT NULL,
  `state` int NOT NULL,
  PRIMARY KEY (`node_id`),
  UNIQUE KEY `actuator_information_node_id_UNIQUE` (`node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `rule`
--

DROP TABLE IF EXISTS `rule`;
CREATE TABLE `rule` (
  `hive_id` int NOT NULL,
  `polling_time` int unsigned NOT NULL,
  `rules` TEXT,
  PRIMARY KEY (`hive_id`),
  UNIQUE KEY `rule_hive_id_UNIQUE` (`hive_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
