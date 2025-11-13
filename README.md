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

- **Scopo:** Generatore di laboratori Kathará/FRR che crea directory per router, host e server WWW, produce file `startup` e configurazioni FRR (`etc/frr/frr.conf`) automaticamente.

**Funzionamento veloce**
- Modalità interattiva: esegui `python3 labGenerator.py` e segui i prompt per creare router, host e WWW.


**Output principali**
- Per ogni router creato: directory `/<lab>/<router>/etc/frr/` contenente `frr.conf` e `vtysh.conf`, oltre a `<router>.startup` nella root del lab.
- Per host/www: file `<name>.startup` e, per WWW, `var/www/html/index.html`.


---

### 🧠 Notes
All labs are designed for the **Kathara network emulation environment**.  
Each folder includes its own `lab.conf` topology file and startup configuration scripts for routers, switches, and hosts.

---

### 🏫 Author
**Diego** – Computer Engineering student at *Roma Tre University*  
**Born from an idea by Rainer Cabral Ilao**

