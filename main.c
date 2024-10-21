#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/sysinfo.h>

int main(int argc, char *argv[]){

    if (argc <= 1 || argc > 2) {
        printf("Usage: %s [size in mb]\n", argv[0]);
        return 1;
    }

    int size = atoi(argv[1]);
    unsigned long length = size * 1024 * 1024;

    struct sysinfo info;
    if (sysinfo(&info) != 0) {
        perror("sysinfo");
    }

    unsigned long long freeRamStart = info.freeram;

    void *ptr;
    int count = 0;

    while (1) {

        ptr = malloc(length);
        if (ptr == NULL) {
            printf("Memory allocation failed after %d MB\n", count * 10);
            break;
        }
        memset(ptr, 0, length);

        printf("Allocated %lu MB\n", length);

        usleep(100000); // 100 ms

        if (sysinfo(&info) != 0) {
            perror("sysinfo");
            break;
        }


        if ((double) info.freeram <= 0.3 * (double) freeRamStart && count == 0) {
            length /= 2;
            count++;
        }else if ((double) info.freeram <= 0.2 * (double) freeRamStart && count == 1) {
            length /= 2;
            count++;
        }else if ((double) info.freeram <= 0.1 * (double) freeRamStart && count == 2) {
            length /= 2;
            count++;
        }

    }

    return 0;
}
