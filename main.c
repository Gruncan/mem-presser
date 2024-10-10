#include <unistd.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>


int main(int argc, char *argv[]){

    if (argc <= 1 || argc > 2) {
        printf("Usage: %s [size in mb]\n", argv[0]);
        return 1;
    }

    int size = atoi(argv[1]);

    size_t length = size * 1024 * 1024;
    void* ptr = mmap(NULL, length, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    if(ptr == MAP_FAILED){
        perror("Error mapping memory");
        return -1;
    }

    if(madvise(ptr, length, MADV_POPULATE_WRITE) == -1) {
        perror("Error madvising memory");
        return -2;
    }


    while(1) {

    }

    return 0;

}
