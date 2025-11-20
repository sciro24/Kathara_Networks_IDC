# Internet and Data Centers – Kathara Labs

This repository contains a collection of **Kathara** lab exercises developed for the *Internet and Data Centers* course at **Roma Tre University**.  
The labs are used to practice network configuration, routing, and data center design topics covered during the course.

🚀 The repository includes **labGenerator**, a tool designed to help automatically build a complete lab environment, streamlining the creation of all its components.

[🛠️ LAB GENERATOR](#labgenerator)

---

## 📘 Partial Exam 1 – RIP/OSPF Network Configuration

This section contains the labs used to prepare for the **first midterm**, covering **RIP and OSPF routing protocols**.  
The labs focus on configuring routers, understanding basic network topologies, and practicing both single-area and multi-area OSPF scenarios.


**LABS:**

- ⚙️ [BUTTERFLY (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20BUTTERFLY%20%28OSPF%20-%20RIP%29/)
- ⚙️ [CLOUDS (OSPF MULTI-AREA)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20CLOUDS%20%28OSPF%20MULTI-AREA%29/)
- ⚙️ [FALLING ASLEEP (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20FALLING%20ASLEEP%20%28OSPF%20-%20RIP%29/)
- ⚙️ [MARACAS (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20MARACAS%20%28OSPF%20-%20RIP%29/)
- ⚙️ [PUZZLE (OSPF MULTI-AREA)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20PUZZLE%20%28OSPF%20MULTI-AREA%29/)
- ⚙️ [STREET LIGHT (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20STREET%20LIGHT%20%28OSPF%20-%20RIP%29/)
- ⚙️ [TENNIS (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20TENNIS%20%28OSPF%20-%20RIP%29/)
- ⚙️ [TWIN PAN BALANCE (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20TWIN%20PAN%20BALANCE%20%28OSPF%20-%20RIP%29/)
- ⚙️ [UP ARROW OSPF (RIP 2 BORDER)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20UP%20ARROW%20OSPF%20%20%28RIP%202%20BORDER%29/)




---

## 🌐 Partial Exam 2 – BGP w/ Policy

This section includes the labs used to prepare for the **second midterm**, focused on the **BGP** (Border Gateway Protocol) and routing **policy** configuration.
The exercises cover BGP setup in multi-AS environments, route filtering and preference management, and the implementation of import/export policies to control inter-domain traffic behavior.


**LABS:**
- ⚙️ [CANDY (BGP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20CANDY%20%28BGP%29/)
- ⚙️ [DESCONOCIDA (BGP - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20DESCONOCIDA%20%28BGP%20-%20RIP%29/)
- ⚙️ [GALAXY (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20GALAXY%20%28BGP%20-%20OSPF%20-%20RIP%29/)
- ⚙️ [INCOGNITA (BGP - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20INCOGNITA%20%28BGP%20-%20RIP%29/)
- ⚙️ [PEAR TO PEAR (BGP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20PEAR%20TO%20PEAR%20%28BGP%29/)
- ⚙️ [RED BARON (BGP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20RED%20BARON%20%28BGP%29/)
- ⚙️ [T1-C2 (BGP - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20T1-C2%20%28BGP%20-%20RIP%29/)
- ⚙️ [T2-C1 (BGP - OSPF)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20T2-C1%20%28BGP%20-%20OSPF%29/)
- ⚙️ [TROUSERS (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20TROUSERS%20%28BGP%20-%20OSPF%20-%20RIP%29/)
- ⚙️ [HOUR GLASS (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20HOUR%20GLASS%20%28BGP%20-%20OSPF%20-%20RIP%29/)
- ⚙️ [PAPILLON (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20PAPILLON%20%28BGP%20-%20OSPF%20-%20RIP%29/)




---

## 🧩 Partial Exam 3 – DNS

This section includes the labs used to prepare for the **third midterm**, focused on **BGP**, **IGP** (OSPF/RIP), and **DNS** configuration.
The exercises cover multi-protocol routing setup, inter-domain and intra-domain traffic management, and the deployment and troubleshooting of DNS services in a networked environment.


**LABS:**
- ⚙️










---

## ☁️ Partial Exam 4 – 









---

# LabGenerator

## 📋 Description

`labGenerator.py` is an interactive Python tool designed to automate the creation of **Kathara labs** for complex network emulation. The tool significantly simplifies the process of configuring routers, hosts, web servers, and DNS servers, automatically generating all the necessary configuration files for routing protocols (**BGP, OSPF, RIP**) using **FRRouting (FRR)**.

---

## ✨ Key Features

### 🔧 Operating Modes

The generator supports various operating modes:

1.  **Interactive Creation** - Creates a new lab step-by-step with guided assistance.
2.  **File Import** - Imports existing configurations from XML/JSON files.
3.  **XML Regeneration** - Rebuilds the metadata XML file from an existing lab.
4.  **PING Command Generation** - Automatically creates ping commands to test connectivity between all devices.
5.  **DNS Configuration** - Assigns customized `resolv.conf` files to devices.
6.  **Loopback Management** - Adds loopback interfaces to existing devices.
7.  **BGP Policy** - Applies advanced BGP policies (**access-list, prefix-list, route-map, customer-provider**).

### 📦 Supported Components

* **FRR Router**: Automatic configuration with support for:
    * **BGP** (Border Gateway Protocol)
    * **OSPF** (Open Shortest Path First) - single-area and multi-area
    * **RIP** (Routing Information Protocol)
    * Static Routing
    * Automatic network aggregation
    * Advanced BGP policies

* **Host**: Endpoint devices with IP and gateway configuration:
    * Multiple interface support
    * Customizable static routes

* **WWW Server**: Apache server with custom HTML pages:
    * Automatic `index.html` generation
    * IP and routing configuration

* **DNS Server (BIND9)**: Full-featured DNS server support:
    * Root server or recursive resolver
    * Custom authoritative zones
    * Configurable forwarders
    * A, NS, CNAME, PTR records

---

## 🚀 Tool Usage

### Prerequisites

* Python 3.x
* Kathara installed
* Docker installed

### Run

To start the tool, run the following command in your terminal:

```bash
python3 labGenerator.py
```

### Main Menu

When launched in interactive mode, the tool presents the following options:

```
C - Crea nuovo laboratorio (interattivo)
I - Importa da file (XML/JSON)
R - Rigenera XML di un lab esistente
G - Genera comando PING per un lab esistente
A - Assegna un file resolv.conf specifico a un dispositivo
L - Aggiungi loopback a dispositivo in un lab esistente
P - Applica Policies BGP
Q - Esci
```


---

---

### 🏫 Author
**Diego** – Computer Engineering student at *Roma Tre University*  
*Born from an idea by Rainer Cabral Ilao*

