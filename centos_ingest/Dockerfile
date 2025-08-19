# Base compatible con CentOS (RHEL like) y multi-arch estable
FROM rockylinux:9

RUN dnf -y update && dnf -y install postgresql && dnf clean all

WORKDIR /opt/app
COPY ingest.sh /opt/app/ingest.sh
COPY normalize.sql /opt/app/normalize.sql

# Evitar problemas de fin de línea (CRLF) y dar permisos
RUN sed -i 's/\r$//' /opt/app/ingest.sh && chmod +x /opt/app/ingest.sh

CMD ["/opt/app/ingest.sh"]
