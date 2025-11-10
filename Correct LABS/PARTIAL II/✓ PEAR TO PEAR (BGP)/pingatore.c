#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int checkFile(char*);
char* leggiRiga(char*);
int carattereBuono(char);
int checkIndirizzo(char*);
char** leggiFile(char*, char**, int* ind);
void generaFile(char**, int dim);

int main(int argc, char* argv[]) {
    char** indirizzi = NULL;
    int inx = 0;
    int ind;
    if (argc == 1) {
        printf("Nessun file inserito!\n");
        return 1;
    }
        
    for (ind = 1; ind < argc; ind++) {
        //if (checkFile(argv[ind])) {
            indirizzi = leggiFile(argv[ind], indirizzi, &inx);
            printf("Il file \'%s\' e\' stato letto!\n", argv[ind]);
        //} else {
           // printf("Il file \'%s\' e\' stato scartato!\n", argv[ind]);
        //}
    }

    generaFile(indirizzi, inx);
    
    for (ind = 0; ind < inx; ind++) {
        free(indirizzi[ind]);
    }
    free(indirizzi);
    return 0;
}

int checkFile(char* nomeFile) {
    int ind = 0;
    int inx = 0;
    char estensione[100];
    int flag = 0;
    while (nomeFile[ind] != '\0') {
        if (!flag) {
           if (nomeFile[ind] == '.') {
            flag = 1;
           } else {
            ind++;
           continue; 
           }   
        }
        estensione[inx] = nomeFile[ind];
        ind++;
        inx++;
    }
    if (strcmp(estensione, ".startup") == 1) {
        return 1;
    }
    return 0;
}

char* leggiRiga(char* riga) {
    int ind = 0, inx = 0;
    int flag = 0;
    char* indirizzo = (char*) calloc(16, sizeof(char));

    while (riga[ind] != '\0' && inx < 15) {
        char carattere = riga[ind];
        if (carattereBuono(carattere)) {
            indirizzo[inx] = carattere;
            inx++;
            flag = 1;
        } else if (flag) {
            break;
        }
        ind++;
    }
    indirizzo[inx] = '\0';
    return indirizzo;
}

int carattereBuono(char carattere) {
    return (carattere >= '0' && carattere <= '9') || (carattere == '.');
}

int checkIndirizzo(char* indirizzo) {
    int num, conta = 0, ind = 0, corretto = 1;
    char numStr[4];

    while (corretto && indirizzo[ind] != '\0') {
        int inx = 0;
        while (indirizzo[ind] != '.' && indirizzo[ind] != '\0' && inx < 3) {
            numStr[inx++] = indirizzo[ind++];
        }
        numStr[inx] = '\0';
        num = atoi(numStr);

        if (num < 0 || num > 255) {
            corretto = 0;
        } else {
            conta++;
        }
        if (indirizzo[ind] == '.') ind++;
    }
    return corretto && (conta == 4);
}

char** leggiFile(char* nomeFile, char** indirizzi, int* inx) {
    char* riga = (char*) malloc(100 * sizeof(char));
    char* indirizzo;
    FILE* file = fopen(nomeFile, "r");

    if (file == NULL) {
        printf("Apertura del file \'%s\' non riuscita!\n", nomeFile);
        free(riga);
        return indirizzi;
    }

    while (fscanf(file, "%99s\n", riga) > 0) {
        indirizzo = leggiRiga(riga);
        if (checkIndirizzo(indirizzo)) {
            indirizzi = (char**) realloc(indirizzi, (*inx + 1) * sizeof(char*));
            indirizzi[*inx] = indirizzo;
            (*inx)++;
        } else {
            free(indirizzo); // Libera l'indirizzo non valido
        }
    }
    
    free(riga);
    fclose(file);

    return indirizzi;
}

void generaFile(char** indirizzi, int dim){
    FILE* stampa = fopen("indirizzi.sh", "w");
    int ind;

    fprintf(stampa, "#!/bin/sh\n");
    for (ind = 0; ind<dim; ind++) {
        fprintf(stampa, "timeout 1s ping -c 1 %s\n", indirizzi[ind]);
    }

    printf("Il file \'indirizzi.sh\' e\' stato creato correttamente!\n");

}
