/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
/* created by: jordan bonecutter * * * * * * * * * * * * * * * * */
/* copyright © all rights reserved * * * * * * * * * * * * * * * */
/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include <stdio.h>

int main(int argc, char** argv)
{
	FILE *fp;
	char c;
	fp = fopen(argv[1], "r");

	fseek(fp, -10, SEEK_END);
	while((c = fgetc(fp)) != EOF)
		printf("%c\n", c);
	fclose(fp);
	return 0;
}
