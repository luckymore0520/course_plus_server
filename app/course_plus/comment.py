#coding=utf-8
from flask import Flask, jsonify, abort, g, make_response, request , url_for
from flask.ext.restful import Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from app import app,db,api,auth
import json
import datetime
from simple_result import SimpleResult
from user import User


class Comment(db.Model):
    __tablename__ = 't_comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deleteAt = db.Column(db.DateTime)
    topicId = db.Column(db.Integer, ForeignKey('t_topic.id'))
    userId = db.Column(db.Integer, ForeignKey('t_user.id'))
    parentId = db.Column(db.Integer, ForeignKey('t_comment.id'))
    rootId = db.Column(db.Integer, ForeignKey('t_comment.id'))


    def replyCount(self):
        return 0

    def author(self):
        author = User.query.get(self.userId)
        return author

    def json(self):
        author = self.author()
        return {
            "id":self.id,
            "content":self.content,
            "replyCount":self.replyCount(),
            "parentId":self.parentId,
            "rootId":self.rootId,
            "replyTime":self.createdAt.strftime('%Y-%m-%d %H:%M:%S'),
            "authorName":author.nickname,
            "authorIcon":author.icon,
            "authorId":self.userId
        }

@app.route('/api/user/comment/postComment', methods=['POST'])
@auth.login_required
def postComment():
    content = request.json.get("content")
    replyId = request.json.get("replyId")
    topicId = request.json.get("topicId")
    user = g.user
    if not topicId or not content:
        abort(400)
    comment = Comment()
    comment.content = content
    comment.parentId = replyId
    comment.topicId = topicId
    comment.createdAt = datetime.datetime.now()
    comment.updatedAt = comment.createdAt
    comment.rootId = findCommentRootId(replyId)    
    comment.userId = user.id
    db.session.add(comment)
    db.session.commit() 
    return (jsonify(SimpleResult(0,"发布成功").json()),200)

@app.route('/api/web/comment/getCommentList', methods=['GET'])
def getCommentList():
    page = request.args.get("page")
    limit = request.args.get("limit",20)
    comment_id = request.args.get("comment_id")
    topic_id = request.args.get("topic_id")
    if not page or not topic_id:
        abort(400)
    comments = []
    page = int(page)
    if comment_id:
        comments = db.session.query(Comment).filter(Comment.rootId == comment_id,Comment.topicId == topic_id).limit(limit).offset(limit * (page-1))
    else:
        comments = db.session.query(Comment).filter(Comment.topicId == topic_id,Comment.rootId == None).limit(limit).offset(limit * (page-1))
    commentsJsonList = []
    for comment in comments:
        commentsJsonList.append(comment.json())
    return (json.dumps(commentsJsonList),200)


def findCommentRootId(replyId):
    if (replyId):
        #寻找该评论
        comment = Comment.query.get(replyId)
        # 如果该评论有父节点，寻找评论父节点
        if comment.parentId:
            return findCommentRootId(comment.parentId)
        else:
            return replyId
    return None


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)