import clr
import System
clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")
import RevitServices
from Autodesk.Revit.ApplicationServices import Application
from Autodesk.Revit import DB
from Autodesk.Revit.DB import DirectShape as ds
from System.Collections.Generic import List


with DB.Transaction(doc,"qwe") as t:
    t.Start()
    cat_id = DB.ElementId(DB.BuiltInCategory.OST_MechanicalEquipment)
    id_les = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Stairs).WhereElementIsNotElementType().ToElements()[0]
    opt = DB.Options()
    lt = List[DB.GeometryObject]
    x = id_les.get_Geometry(opt).GetEnumerator()
    lt = List[DB.GeometryObject] (
        geom for geom in x
    )

    ds1 = ds.CreateElement(doc,cat_id)
    ds1.SetShape(lt)
    print(x)


    t.Commit()
