#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define BUFFER_SIZE 1024

static int count = 0;


void* inf_recursive(void* buffer, size_t size) {
    if (size < 0) return buffer;

    char new_buffer[size];

    memset(new_buffer, 0, size);

    usleep(100000);
    count++;
    printf("Allocations: %d\n", count);
    inf_recursive(new_buffer, size);

}





int main(int argc, char *argv[]){

    if (argc <= 1 || argc > 2) {
        printf("Usage: %s [size in kb]\n", argv[0]);
        return 1;
    }

    int size = atoi(argv[1]);
    unsigned long length = size * 512;

    char inital[length];
    inf_recursive(inital, length);

    return 0;
}
