import clr
import System
clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")

import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from Autodesk.Revit import DB
from Autodesk.Revit.DB import FilteredElementCollector as FEC
from Autodesk.Revit.DB import FamilyInstance as FI
from Autodesk.Revit.DB.Mechanical import Duct
from Autodesk.Revit.DB.Plumbing import Pipe

from System.Collections.Generic import List

#Вводные параметры
level = UnwrapElement(IN[0])
value_switch = IN[1]

doc = DocumentManager.Instance.CurrentDBDocument
 
# Обработка уровней

def switch_level (lvl, value):

    if type(lvl) != DB.Level:
        return
    
    high_param = lvl.get_Parameter(DB.BuiltInParameter.LEVEL_ELEV)
    if not high_param:
        return
    
    try:
        high_double = high_param.AsDouble()
        high_param.Set(high_double+(value/304.8))
    except:
        pass
        

# Обработка экземпляров семейств

def switch_family_instance(value):
    instances = [item
            for item
            in (FEC(doc).
                OfClass(FI).
                WhereElementIsNotElementType().
                ToElements())
            if item.LevelId == level.Id]
    for ins in instances:

        if ins.SuperComponent != None or ins.Host != None:
            continue

        high_param = ins.get_Parameter(DB.BuiltInParameter.INSTANCE_ELEVATION_PARAM)
        if not high_param:
            return
        
        try:
            high_double = high_param.AsDouble()
            high_param.Set(high_double-(value/304.8))
        except:
            continue



#Обработка кривых (трубы, воздуховоды, гибкие трубы/воздуховоды)  

def switch_curve_fam(value):

    cats = [DB.BuiltInCategory.OST_PipeCurves,
            DB.BuiltInCategory.OST_DuctCurves,
            DB.BuiltInCategory.OST_FlexPipeCurves,
            DB.BuiltInCategory.OST_FlexDuctCurves]
    
    catId = List [DB.BuiltInCategory](cats)
    catFilt = DB.ElementMulticategoryFilter(catId)

    curves = [item
            for item
            in (FEC(doc).
                WherePasses(catFilt).
                WhereElementIsNotElementType().
                ToElements())
            if item.ReferenceLevel.Id == level.Id]
    for curv in curves:
        high_param = curv.get_Parameter(DB.BuiltInParameter.RBS_OFFSET_PARAM)
        if not high_param:
            return
        try:
            high_double = high_param.AsDouble()
            high_param.Set(high_double-(value/304.8))
        except:
            continue
        
    

TransactionManager.Instance.EnsureInTransaction(doc)

switch_level(level, value_switch)
switch_family_instance(value_switch)
switch_curve_fam(value_switch)


TransactionManager.Instance.TransactionTaskDone()


