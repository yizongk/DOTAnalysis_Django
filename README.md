# This is DOT Analytics Django Web Apps repository

Includes:
 * Performance Indicator
 * Org Chart Portal
 * Daily Potholes

## To install dependencies

By extension, when installing mod_wsgi, you will need Microsoft Visual C++ 14.0 installed on your system. To download it, download the installer with the following link, and select 'Microsoft C++ Build Tools' in the menu of the installer to install the proper dependency

    https://visualstudio.microsoft.com/visual-cpp-build-tools/

Then run the following command
```
python -m pip install -r DOTAnalytics/python_dependencies.txt
```


# Database driver
This web app uses "SQL Server Native Client 11.0", so install it here: https://www.microsoft.com/en-us/download/details.aspx?id=50402

# Database
Need SQL Server Account, need to be of the following roles:
* db_datareader
* db_datawriter
* db_ddladmin (For DDL privilege, such as CREATE, DROP, ALTER TRUNCATE, and RENAME)
* Need Default schema to be 'dbo', to allow creation of tables under the name dbo, like dbo.sessions.