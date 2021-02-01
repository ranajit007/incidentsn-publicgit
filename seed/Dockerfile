FROM mongo
LABEL "author"="Daniel Nava / Jorge Bustillos"
LABEL "company"="IBM"
#Copy init scripts
COPY init/*.sh /docker-entrypoint-initdb.d/
COPY init/*.js /docker-entrypoint-initdb.d/
#Copy seed files if available
ADD /files/*.json /seed/files
#Expose port
EXPOSE 27017