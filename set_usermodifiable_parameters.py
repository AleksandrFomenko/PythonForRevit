import clr
import System
clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")
import RevitServices
from Autodesk.Revit.ApplicationServices import Application
from Autodesk.Revit import DB


docm = doc.FamilyManager
with DB.Transaction(doc,"qwe") as t:
    t.Start()
    for parameter in docm.GetParameters():
        if parameter.Definition.Name == "":
            docm.Set(parameter,DB.ElementId())
    t.Commit()
