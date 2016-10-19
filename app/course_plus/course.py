#coding=utf-8
from flask import Flask, jsonify, abort, g, make_response, request , url_for
from flask.ext.restful import Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from app import app,db,api
import json
import datetime


class School(db.Model):
    __tablename__ = 't_school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    createdAt = db.Column(db.DateTime)
    updateAt = db.Column(db.DateTime)
    deleteAt = db.Column(db.DateTime)
    specialities = relationship("Speciality", backref = "School")

class Speciality(db.Model):
    __tablename__ = 't_speciality'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    createdAt = db.Column(db.DateTime)
    updateAt = db.Column(db.DateTime)
    deleteAt = db.Column(db.DateTime)
    schoolId = db.Column(db.Integer, ForeignKey('t_school.id'))
    courses = relationship("Course", backref = "Speciality")
    def json(self):
        return {"name":self.name, "id":self.id}


class Course(db.Model):
    __tablename__ = 't_course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16))
    introduction = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updateAt = db.Column(db.DateTime)
    deleteAt = db.Column(db.DateTime)
    specialityId = db.Column(db.Integer, ForeignKey('t_speciality.id'))

    def topicNum(self):
        return 0

    def resourceNum(self):
        return 0

    def schoolName(self):
        return "南京大学"

    def specialityName(self):
        speciality = Speciality.query.get(self.specialityId)
        if speciality:
            return speciality.name
        return ""

    def authors(self):
        return []

    def simpleJson(self):
        return {"id":self.id,
        "name":self.name,
        "topicNum":self.topicNum(),
        "resourceNum":self.resourceNum(),
        "schoolName":self.schoolName(),
        "specialityName":self.specialityName(),
        "specialityId":self.specialityId,
        "authors":self.authors()}


@app.route('/api/web/course/speciality', methods=['GET'])
def getSpecialList():
    schools = db.session.query(School).all()
    specialDic = {}
    for school in schools:
        schoolDic = {"id":school.id}
        specialityJsonList = []
        specialityList = Speciality.query.filter_by(school_id = school.id)
        for speciality in specialityList:
            specialityJsonList.append(speciality.json())
        schoolDic["specialities"] = specialityJsonList
        specialDic[school.name] = schoolDic
    return (jsonify(specialDic),200)

@app.route('/api/web/course/courseList', methods=['GET'])
def getCourseList():
    page = int(request.args.get("page"))
    limit = request.args.get("limit",20)
    key = request.args.get("key")
    courses = []
    if not page:
        abort(400)
    courses = []
    if key:
        courses = db.session.query(Course).filter(Course.name.like("%"+key+"%")).limit(limit).offset(limit * (page-1))
    else:
        courses = db.session.query(Course).limit(limit).offset(limit * (page-1))
    courseJsonList = []
    for course in courses:
        courseJsonList.append(course.simpleJson())
    print(courseJsonList)
    return (json.dumps(courseJsonList),200)





