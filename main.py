#!/usr/bin/env python
from credentials import Credentials
from constructs import Construct
from cdktf import App, TerraformStack, TerraformResourceLifecycle, Token
from cdktf import App, NamedRemoteWorkspace, TerraformStack, TerraformOutput, RemoteBackend
from imports.aws.provider import AwsProvider
from imports.aws.subnet import Subnet
from imports.aws.key_pair import KeyPair
from imports.aws.internet_gateway import InternetGateway 
from imports.aws.route_table import RouteTable, RouteTableRoute
from imports.aws.route_table_association import RouteTableAssociation
from imports.aws.lb import Lb
from imports.aws.lb_target_group import LbTargetGroup, LbTargetGroupHealthCheck
from imports.aws.lb_target_group_attachment import LbTargetGroupAttachment
from imports.aws.lb_listener import LbListener, LbListenerDefaultAction
from imports.aws.security_group import SecurityGroup, SecurityGroupEgress, SecurityGroupIngress
from imports.aws.eip import Eip
from imports.aws.db_instance import DbInstance
from imports.aws.db_subnet_group import DbSubnetGroup
from imports.aws.vpc import Vpc
from imports.aws.launch_configuration import LaunchConfiguration
from imports.aws.autoscaling_group import AutoscalingGroup
from imports.aws.autoscaling_attachment import AutoscalingAttachment
from imports.aws.route53_record import Route53Record, Route53RecordAlias



class AndreBrambillaProject(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # define resources here
        AwsProvider(self, "AWS", region=Credentials.REGION, access_key=Credentials.ACCESS_KEY, secret_key=Credentials.SECRET_KEY)
        
        # Creating the VPC with CIDR 10.0.0.0/16 - Netmask:255.255.0.0, TotalHosts:65536
        vpc_web_main = Vpc(
            self,
            "vpc_web_main",
            cidr_block="10.0.0.0/16",
            tags={"Name": "vpc_web_main"}
        )

        # Public Subnet - Mask:255.255.255.0, TotalHosts:256
        pub_subnet = Subnet(
            self,
            "public_subnet",
            vpc_id=vpc_web_main.id,
            cidr_block="10.0.1.0/24",
            availability_zone="eu-west-1a",
            map_public_ip_on_launch=True,
            tags={"Name": "public_subnet_tfg"}
        )


        # Public Subnet 2 - Mask:255.255.255.0, TotalHosts:256
        pub_subnet_2 = Subnet(
            self,
            "public_subnet_tfg_2",
            vpc_id=vpc_web_main.id,
            cidr_block="10.0.2.0/24",
            availability_zone="eu-west-1b",
            map_public_ip_on_launch=True,
            tags={"Name": "public_subnet_tfg_2"}
        )

        priv_subnet = Subnet(
            self,
            "priv_subnet_tfg",
            vpc_id=vpc_web_main.id,
            cidr_block="10.0.3.0/24",
            availability_zone="eu-west-1a",
            tags={"Name": "priv_subnet_tfg_2"}
        )

        priv_subnet_2 = Subnet(
            self,
            "priv_subnet_tfg_2",
            vpc_id=vpc_web_main.id,
            cidr_block="10.0.4.0/24",
            availability_zone="eu-west-1b",
            tags={"Name": "priv_subnet_tfg_2"}
        )

        ingress_rule_web = SecurityGroupIngress(
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"]
        )

        ingress_rule_ssh = SecurityGroupIngress(
            cidr_blocks=["0.0.0.0/0"],
            from_port=22,
            to_port=22,
            protocol="tcp"
        ) 

        egress_rule_web = SecurityGroupEgress(
            cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=0,
            protocol="-1"
        )

        ingress_rule_rds = SecurityGroupIngress(
            cidr_blocks=["0.0.0.0/0"],
            from_port=3306,
            to_port=3306,
            protocol="tcp"
        )
        # Security Groups

        allow_web_rules = SecurityGroup(self, "allow_web_rules",
            vpc_id=vpc_web_main.id,
            ingress=[ingress_rule_web,ingress_rule_ssh],
            egress=[egress_rule_web]
        )

        allow_rds_rules = SecurityGroup(self, "allow_rds_rules",
            vpc_id=vpc_web_main.id,
            ingress=[ingress_rule_rds]
        )

        # internet Gateway

        igw_web = InternetGateway(self, "igw_web",
            tags={
                "Name": "igw_web"
            },
            vpc_id=vpc_web_main.id
        )

        # Route Table
        route_table_web = RouteTable(self, "route_table_web",
            route=[RouteTableRoute(
                cidr_block="0.0.0.0/0",
                gateway_id=igw_web.id
            )
            ],
            vpc_id=vpc_web_main.id,
            
        )
        # Route Table Association
        route_table_association = RouteTableAssociation(self, "a",
            route_table_id=route_table_web.id,
            subnet_id=pub_subnet.id
        )
        route_table_association_b = RouteTableAssociation(self, "b",
            route_table_id=route_table_web.id,
            subnet_id=pub_subnet_2.id
        )

        # keypairs
        key_pairs = KeyPair(self, "key_pairs",
            key_name="instanceskeypairs",
            public_key=Credentials.KEY_PAIR
        )

        # Load Balancer
        load_balancer = Lb(self, "load_balancer",
            name="loadbalancertfg",
            load_balancer_type="application",
            security_groups=[allow_web_rules.id],
            subnets=[pub_subnet.id, pub_subnet_2.id]
        )

        # Target Groups

        target_group = LbTargetGroup(self,"target_group",
        name="targetgrouptfg",
        port=80,
        protocol="HTTP",
        vpc_id=vpc_web_main.id,
        target_type="instance",
        health_check=LbTargetGroupHealthCheck(
            enabled=True,
            matcher="200",
            path="/",
            port="80",
            protocol="HTTP"
        )
        )

        load_balancer_listener = LbListener(self, "lb_listener", 
            load_balancer_arn=load_balancer.arn,
            port=80,
            protocol="HTTP",
            default_action=[LbListenerDefaultAction(
                target_group_arn=target_group.arn,
                type="forward"
            )]
        )
        # RDS MySQL Instance
        # Variables
        rds_endpoint= rds_output.value
        rds_user = Credentials.RDS_USER
        rds_password= Credentials.RDS_PASSWORD
        rds_database = Credentials.RDS_DATABASE
        git_token = Credentials.GIT_TOKEN

        rds_subnetgroup = DbSubnetGroup(self,"rds_subnetgroup",
            subnet_ids=[priv_subnet.id,priv_subnet_2.id],
            name="rds_subnetgroup"
        )

        rds_instance = DbInstance(self,"rds_instance",
            allocated_storage=20,
            engine="mysql",
            engine_version="8.0.35",
            instance_class="db.t3.micro",
            db_name=rds_database,
            username=rds_user,
            password=rds_password,
            storage_type="gp2",
            vpc_security_group_ids=[allow_rds_rules.id],
            skip_final_snapshot=True,
            db_subnet_group_name=rds_subnetgroup.name
        )

        #Output RDS
        rds_output = TerraformOutput(self, "endpoint_db", value=rds_instance.endpoint)
        
        # Launch Configuration
        web_launch_config = LaunchConfiguration(self, "web_launch_config",
            name_prefix="web_launch_config",
            image_id="ami-0905a3c97561e0b69",
            instance_type="t2.micro",
            lifecycle=TerraformResourceLifecycle(
                create_before_destroy=True
            ),
            user_data=f"""#!/bin/bash
                            rds_endpoint={rds_endpoint}
                            endpoint_wo_port=$(echo "$rds_endpoint" | sed 's/:.*//')
                            echo RDS_ENDPOINT_WO_PORT=$endpoint_wo_port >> /home/ubuntu/variables
                            echo RDS_ENDPOINT={rds_endpoint} >> /home/ubuntu/variables
                            echo RDS_USER={rds_user} >> /home/ubuntu/variables
                            echo RDS_PASSWORD={rds_password} >> /home/ubuntu/variables
                            echo RDS_DATABASE={rds_database} >> /home/ubuntu/variables
                            source /home/ubuntu/variables
                            apt update -y
                            apt upgrade -y
                            apt install mysql-client -y
                            apt install apache2 libapache2-mod-php8.1 -y
                            apt install php libapache2-mod-php php-mysql -y
                            apt install php-curl php-gd php-mbstring php-xml php-xmlrpc php-soap php-intl php-zip -y
                            ufw allow Apache
                            ufw reload
                            git clone https://{git_token}@github.com/andrebrambillaf/github-web-code.git /tmp/repo
                            mv /tmp/repo/* /var/www/html
                            mysql -u $RDS_USER -p$RDS_PASSWORD -h $RDS_ENDPOINT_WO_PORT -D $RDS_DATABASE -e "CREATE TABLE IF NOT EXISTS contactdata (id int(11) NOT NULL AUTO_INCREMENT, firstname varchar(55) NOT NULL, lastname varchar(55) NOT NULL, phone varchar(15) NOT NULL, email varchar(55) NOT NULL, message text NOT NULL, PRIMARY KEY (id)) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1; COMMIT;"
                            cp /home/ubuntu/variables /var/www/html/.env
                            systemctl restart apache2
                            chown -R ubuntu:ubuntu /var/www/html""",
            key_name="instanceskeypairs",
            security_groups=[allow_web_rules.id],
            depends_on=[rds_instance]
        )

        # Auto Scaling Group

        web_autoscaling_group = AutoscalingGroup(self, "web_autoscaling_group",
            desired_capacity=1,
            max_size=4,
            min_size=1,
            vpc_zone_identifier=[pub_subnet.id,pub_subnet_2.id],
            launch_configuration=web_launch_config.name,
            target_group_arns=[target_group.arn],
            health_check_grace_period=300,
            health_check_type="EC2",
            depends_on=[web_launch_config]
        )

        asg_attachment = AutoscalingAttachment(self, "asg_attachment",
        depends_on=[target_group],
        autoscaling_group_name=web_autoscaling_group.name,
        lb_target_group_arn=target_group.arn                                          
        )

        # Route53
        route53_dns = Route53Record(self, "route53_dns",
            zone_id=Credentials.ZONE_ID,
            name=Credentials.NAME_RECORD,
            records=[load_balancer.dns_name],
            ttl=120,
            type="CNAME"
        )

        # Outputs
        TerraformOutput(self, "vpc_web_main_id", value=vpc_web_main.id)
        TerraformOutput(self, "endpoint_db_1", value=rds_instance.endpoint)
app = App()
AndreBrambillaProject(app, "ufv-cdktf")

app.synth()
